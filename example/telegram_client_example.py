"""
Esempio di client per testare l'API con integrazione Telegram
Mostra come utilizzare tutti gli endpoint dell'API

Prerequisiti:
1. Configurare .env con STEEM_USERNAME, STEEM_WIF, TELEGRAM_BOT_TOKEN
2. pip install -r requirements.txt
3. Avviare il server: python main.py
4. Eseguire questo client: python telegram_client_example.py
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, List

class SteemImageUploadClient:
    """Client per testare l'API di upload immagini con supporto Telegram"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:5000"):
        self.api_url = api_url.rstrip('/')
    
    def get_api_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sull'API"""
        try:
            response = requests.get(f"{self.api_url}/")
            return response.json()
        except Exception as e:
            return {"error": f"Errore connessione: {e}"}
    
    def health_check(self) -> Dict[str, Any]:
        """Controlla stato dell'API"""
        try:
            response = requests.get(f"{self.api_url}/health")
            return response.json()
        except Exception as e:
            return {"error": f"Errore connessione: {e}"}
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Upload diretto di un file locale"""
        if not os.path.exists(file_path):
            return {"error": f"File non trovato: {file_path}"}
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(f"{self.api_url}/upload", files=files)
                return response.json()
        except Exception as e:
            return {"error": f"Errore upload: {e}"}
    
    def upload_telegram_file(self, file_id: str) -> Dict[str, Any]:
        """Upload di un file da Telegram tramite file_id"""
        try:
            data = {"file_id": file_id}
            response = requests.post(
                f"{self.api_url}/upload-telegram", 
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            return {"error": f"Errore upload Telegram: {e}"}
    
    def upload_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Upload multipli file"""
        existing_files = [fp for fp in file_paths if os.path.exists(fp)]
        
        if not existing_files:
            return {"error": "Nessun file esistente trovato"}
        
        try:
            files = []
            file_objects = []
            
            for file_path in existing_files:
                f = open(file_path, 'rb')
                file_objects.append(f)
                files.append(('files', (os.path.basename(file_path), f)))
            
            try:
                response = requests.post(f"{self.api_url}/upload-multiple", files=files)
                return response.json()
            finally:
                for f in file_objects:
                    f.close()
                    
        except Exception as e:
            return {"error": f"Errore upload multipli: {e}"}


def print_json_response(data: Dict[str, Any], title: str = "Risposta"):
    """Stampa risposta JSON in formato leggibile"""
    print(f"\n{'='*20} {title} {'='*20}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("="*50)


def find_sample_images() -> List[str]:
    """Trova immagini di esempio nella directory corrente"""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
    files = []
    
    for ext in extensions:
        files.extend(Path('.').glob(ext))
        files.extend(Path('.').glob(ext.upper()))
    
    return [str(f) for f in files]


def test_api_endpoints():
    """Testa tutti gli endpoint dell'API"""
    print("🎯 Test completo API Steem Image Upload")
    print("="*60)
    
    client = SteemImageUploadClient()
    
    # 1. Info API
    print("\n1️⃣ Test informazioni API...")
    api_info = client.get_api_info()
    print_json_response(api_info, "Informazioni API")
    
    # Verifica se l'API è configurata
    if api_info.get("configuration") != "valid":
        print("⚠️ API non configurata correttamente. Controlla il file .env")
        return
    
    # 2. Health check
    print("\n2️⃣ Test health check...")
    health = client.health_check()
    print_json_response(health, "Stato API")
    
    if health.get("status") != "healthy":
        print("⚠️ API non in stato healthy. Impossibile continuare i test.")
        return
    
    # 3. Test upload file locale
    print("\n3️⃣ Test upload file locale...")
    sample_files = find_sample_images()
    
    if sample_files:
        test_file = sample_files[0]
        print(f"📁 Upload file: {test_file}")
        
        upload_result = client.upload_file(test_file)
        print_json_response(upload_result, "Upload File Locale")
        
        if upload_result.get("success"):
            image_url = upload_result["data"]["url"]
            print(f"✅ Immagine caricata: {image_url}")
        else:
            print(f"❌ Upload fallito: {upload_result.get('error')}")
    else:
        print("⚠️ Nessuna immagine trovata per il test upload locale")
    
    # 4. Test upload Telegram (solo se configurato)
    if api_info.get("telegram", {}).get("enabled"):
        print("\n4️⃣ Test upload Telegram...")
        
        # Esempio di file_id (sostituisci con uno reale per testare)
        example_file_id = "BAADBAADrwADBREAAYdO2wN_vFhgAg"  # File_id di esempio
        
        print(f"📱 Test con file_id: {example_file_id}")
        print("💡 Nota: usa un file_id reale ottenuto da un bot Telegram")
        
        telegram_result = client.upload_telegram_file(example_file_id)
        print_json_response(telegram_result, "Upload Telegram")
        
        if not telegram_result.get("success"):
            print("💡 Normale che fallisca con file_id di esempio")
    else:
        print("\n4️⃣ Skip test Telegram (non configurato)")
    
    # 5. Test upload multipli
    if len(sample_files) > 1:
        print("\n5️⃣ Test upload multipli...")
        
        # Prende max 3 file per il test
        test_files = sample_files[:3]
        print(f"📁 Upload {len(test_files)} file: {[Path(f).name for f in test_files]}")
        
        multiple_result = client.upload_multiple_files(test_files)
        print_json_response(multiple_result, "Upload Multipli")
        
        if multiple_result.get("success"):
            successful = multiple_result["data"]["successful_count"]
            print(f"✅ {successful} file caricati con successo")
        else:
            print(f"❌ Upload multipli fallito")
    else:
        print("\n5️⃣ Skip test upload multipli (servono almeno 2 immagini)")
    
    print(f"\n🎊 Test completato!")
    print("💡 Suggerimenti per utilizzo reale:")
    print("   - Configura TELEGRAM_BOT_TOKEN nel .env per testare Telegram")
    print("   - Usa file_id reali ottenuti da messaggi Telegram")
    print("   - Aggiungi più immagini per testare upload multipli")


def telegram_integration_example():
    """Esempio di integrazione con bot Telegram"""
    print("\n🤖 Esempio integrazione bot Telegram")
    print("="*50)
    
    print("""
Per integrare con un bot Telegram:

1. CONFIGURAZIONE BOT:
   - Crea bot con @BotFather
   - Ottieni token e mettilo in TELEGRAM_BOT_TOKEN nel .env
   - Avvia l'API: python main.py

2. NEL TUO BOT TELEGRAM:

from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import requests

async def handle_photo(update: Update, context):
    # Ottieni file_id dalla foto più grande
    photo = update.message.photo[-1]  # Risoluzione più alta
    file_id = photo.file_id
    
    # Chiama la tua API
    response = requests.post(
        'http://127.0.0.1:5000/upload-telegram',
        json={'file_id': file_id}
    )
    
    result = response.json()
    
    if result.get('success'):
        image_url = result['data']['url']
        await update.message.reply_text(f"✅ Immagine caricata: {image_url}")
    else:
        error = result.get('error', 'Errore sconosciuto')
        await update.message.reply_text(f"❌ Errore: {error}")

# Setup bot
app = Application.builder().token("TUO_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()

3. UTILIZZO:
   - Invia foto al bot
   - Il bot ottiene il file_id
   - Chiama /upload-telegram con il file_id
   - Riceve URL dell'immagine su blockchain
   - Può rispondere con l'URL o usarlo per post/commenti
""")


if __name__ == "__main__":
    try:
        # Test completo API
        test_api_endpoints()
        
        # Esempio integrazione Telegram
        telegram_integration_example()
        
    except KeyboardInterrupt:
        print("\n👋 Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante i test: {e}")