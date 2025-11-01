"""
File di esempio per caricare immagini su Steem e creare un endpoint API
per restituire l'URL delle immagini caricate.

Prerequisiti:
- pip install fastapi uvicorn python-multipart python-dotenv
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

# Importa la classe Blockchain dal tuo progetto
from command.basic.steem_request import Blockchain

# Carica le variabili d'ambiente
load_dotenv()

# Inizializza FastAPI
app = FastAPI(
    title="Steem Image Upload API",
    description="API per caricare immagini su Steem blockchain",
    version="1.0.0"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione
STEEM_USERNAME = os.getenv("STEEM_USERNAME")
STEEM_WIF = os.getenv("STEEM_WIF")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Valida le credenziali
if not STEEM_USERNAME or not STEEM_WIF:
    raise ValueError("STEEM_USERNAME e STEEM_WIF devono essere configurati nel file .env")

# Inizializza la blockchain
blockchain = Blockchain()

# Tipi di file supportati
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ImageUploadService:
    """Servizio per gestire l'upload delle immagini"""
    
    def __init__(self):
        self.blockchain = blockchain
        self.username = STEEM_USERNAME
        self.wif = STEEM_WIF
    
    def validate_file(self, file: UploadFile) -> bool:
        """Valida il file caricato"""
        # Controlla l'estensione
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato file non supportato. Formati accettati: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        
        # Controlla il content type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Il file deve essere un'immagine"
            )
        
        return True
    
    async def save_temp_file(self, file: UploadFile) -> str:
        """Salva il file temporaneamente sul disco"""
        # Crea un file temporaneo
        file_extension = Path(file.filename).suffix.lower()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_path = temp_file.name
        
        try:
            # Copia il contenuto del file
            with temp_file as f:
                content = await file.read()
                if len(content) > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Il file è troppo grande. Dimensione massima: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                f.write(content)
            
            return temp_path
        except Exception as e:
            # Pulisce il file temporaneo in caso di errore
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    def upload_to_steem(self, file_path: str) -> dict:
        """Carica l'immagine su Steem"""
        try:
            result = self.blockchain.steem_upload_image(file_path, self.username, self.wif)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Errore durante l'upload su Steem: {str(e)}"
            )
        finally:
            # Pulisce il file temporaneo
            if os.path.exists(file_path):
                os.unlink(file_path)


# Inizializza il servizio
upload_service = ImageUploadService()


@app.get("/")
async def root():
    """Endpoint di base per verificare che l'API funzioni"""
    return {
        "message": "Steem Image Upload API",
        "status": "running",
        "username": STEEM_USERNAME,
        "supported_formats": list(SUPPORTED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024*1024)
    }


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Endpoint per caricare un'immagine su Steem
    
    Returns:
        JSON con l'URL dell'immagine caricata
    """
    # Valida il file
    upload_service.validate_file(file)
    
    # Salva temporaneamente il file
    temp_path = await upload_service.save_temp_file(file)
    
    try:
        # Carica su Steem
        result = upload_service.upload_to_steem(temp_path)
        
        # Estrae l'URL dal risultato
        if isinstance(result, dict) and 'url' in result:
            image_url = result['url']
        elif isinstance(result, str):
            # Assume che il risultato sia direttamente l'URL
            image_url = result
        else:
            # Prova a estrarre l'URL da diversi formati possibili
            image_url = str(result)
        
        return {
            "success": True,
            "message": "Immagine caricata con successo",
            "data": {
                "filename": file.filename,
                "url": image_url,
                "size_bytes": len(await file.read()) if hasattr(file, 'read') else None,
                "uploaded_by": STEEM_USERNAME
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'upload: {str(e)}"
        )


@app.post("/upload-multiple")
async def upload_multiple_images(files: list[UploadFile] = File(...)):
    """
    Endpoint per caricare multiple immagini
    
    Returns:
        JSON con gli URL di tutte le immagini caricate
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Massimo 10 file per volta"
        )
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Valida il file
            upload_service.validate_file(file)
            
            # Salva temporaneamente il file
            temp_path = await upload_service.save_temp_file(file)
            
            # Carica su Steem
            result = upload_service.upload_to_steem(temp_path)
            
            # Estrae l'URL dal risultato
            if isinstance(result, dict) and 'url' in result:
                image_url = result['url']
            elif isinstance(result, str):
                image_url = result
            else:
                image_url = str(result)
            
            results.append({
                "filename": file.filename,
                "url": image_url,
                "success": True
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "success": False
            })
    
    return {
        "success": len(errors) == 0,
        "message": f"Processati {len(files)} file. {len(results)} successi, {len(errors)} errori",
        "data": {
            "successful_uploads": results,
            "failed_uploads": errors,
            "total_files": len(files),
            "successful_count": len(results),
            "failed_count": len(errors)
        }
    }


@app.get("/health")
async def health_check():
    """Endpoint per verificare lo stato dell'API"""
    try:
        # Verifica la connessione alla blockchain
        blockchain.update_node()
        return {
            "status": "healthy",
            "steem_node": getattr(blockchain, 'steem_node', 'unknown'),
            "username": STEEM_USERNAME
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    print(f"🚀 Avvio del server Steem Image Upload API...")
    print(f"📝 Username: {STEEM_USERNAME}")
    print(f"🌐 Server: http://{API_HOST}:{API_PORT}")
    print(f"📚 Docs: http://{API_HOST}:{API_PORT}/docs")
    
    uvicorn.run(
        "image_upload_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )