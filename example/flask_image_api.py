"""
API Flask per caricare immagini su Steem
Versione semplificata che usa Flask invece di FastAPI

Per installare le dipendenze:
pip install flask python-dotenv
"""

import os
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installato. Usa variabili d'ambiente del sistema.")

# Importa la classe Blockchain
from command.basic.steem_request import Blockchain

# Configurazione
STEEM_USERNAME = os.getenv("STEEM_USERNAME", "your_username_here")
STEEM_WIF = os.getenv("STEEM_WIF", "your_wif_here") 
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 5000))

# Tipi di file supportati
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Inizializza Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Inizializza blockchain
blockchain = Blockchain()

def allowed_file(filename):
    """Verifica se il file è di un tipo supportato"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_config():
    """Verifica che le credenziali siano configurate"""
    if STEEM_USERNAME == "your_username_here" or STEEM_WIF == "your_wif_here":
        return False
    return True

@app.route('/')
def home():
    """Endpoint di base"""
    config_valid = validate_config()
    
    return jsonify({
        'message': 'Steem Image Upload API',
        'status': 'running',
        'configuration': 'valid' if config_valid else 'invalid - check .env file',
        'username': STEEM_USERNAME if config_valid else 'not_configured',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
        'endpoints': {
            'upload_single': '/upload (POST)',
            'upload_multiple': '/upload-multiple (POST)',
            'health': '/health (GET)'
        }
    })

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Endpoint per caricare una singola immagine
    
    Form data:
        file: File immagine da caricare
    
    Returns:
        JSON con risultato dell'upload
    """
    # Verifica configurazione
    if not validate_config():
        return jsonify({
            'success': False,
            'error': 'Configurazione non valida. Controlla STEEM_USERNAME e STEEM_WIF nel file .env'
        }), 500
    
    # Controlla se il file è presente nella richiesta
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Nessun file fornito'
        }), 400
    
    file = request.files['file']
    
    # Controlla se è stato selezionato un file
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Nessun file selezionato'
        }), 400
    
    # Verifica il tipo di file
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Formato file non supportato. Formati supportati: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        # Salva il file temporaneamente
        filename = secure_filename(file.filename)
        file_extension = Path(filename).suffix
        
        # Crea un file temporaneo
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_path = temp_file.name
        
        # Salva il file
        file.save(temp_path)
        
        try:
            # Carica su Steem
            print(f"📤 Caricamento {filename} su Steem...")
            result = blockchain.steem_upload_image(temp_path, STEEM_USERNAME, STEEM_WIF)
            
            # Estrae l'URL dal risultato
            if isinstance(result, dict) and 'url' in result:
                image_url = result['url']
            elif isinstance(result, str):
                image_url = result
            else:
                image_url = str(result)
            
            return jsonify({
                'success': True,
                'message': 'Immagine caricata con successo',
                'data': {
                    'filename': filename,
                    'url': image_url,
                    'uploaded_by': STEEM_USERNAME,
                    'result': result
                }
            })
            
        finally:
            # Pulisce il file temporaneo
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore durante l\'upload: {str(e)}'
        }), 500

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_images():
    """
    Endpoint per caricare multiple immagini
    
    Form data:
        files: Lista di file immagine da caricare
    
    Returns:
        JSON con risultati degli upload
    """
    # Verifica configurazione
    if not validate_config():
        return jsonify({
            'success': False,
            'error': 'Configurazione non valida. Controlla STEEM_USERNAME e STEEM_WIF nel file .env'
        }), 500
    
    # Controlla se ci sono file nella richiesta
    if 'files' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Nessun file fornito'
        }), 400
    
    files = request.files.getlist('files')
    
    if len(files) == 0:
        return jsonify({
            'success': False,
            'error': 'Nessun file selezionato'
        }), 400
    
    if len(files) > 10:
        return jsonify({
            'success': False,
            'error': 'Massimo 10 file per volta'
        }), 400
    
    results = []
    errors = []
    
    for file in files:
        if file.filename == '':
            errors.append({
                'filename': 'unnamed_file',
                'error': 'Nome file vuoto',
                'success': False
            })
            continue
        
        if not allowed_file(file.filename):
            errors.append({
                'filename': file.filename,
                'error': f'Formato non supportato',
                'success': False
            })
            continue
        
        try:
            # Salva il file temporaneamente
            filename = secure_filename(file.filename)
            file_extension = Path(filename).suffix
            
            # Crea un file temporaneo
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_path = temp_file.name
            
            # Salva il file
            file.save(temp_path)
            
            try:
                # Carica su Steem
                print(f"📤 Caricamento {filename} su Steem...")
                result = blockchain.steem_upload_image(temp_path, STEEM_USERNAME, STEEM_WIF)
                
                # Estrae l'URL dal risultato
                if isinstance(result, dict) and 'url' in result:
                    image_url = result['url']
                elif isinstance(result, str):
                    image_url = result
                else:
                    image_url = str(result)
                
                results.append({
                    'filename': filename,
                    'url': image_url,
                    'success': True,
                    'result': result
                })
                
            finally:
                # Pulisce il file temporaneo
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        except Exception as e:
            errors.append({
                'filename': file.filename,
                'error': str(e),
                'success': False
            })
    
    return jsonify({
        'success': len(errors) == 0,
        'message': f'Processati {len(files)} file. {len(results)} successi, {len(errors)} errori',
        'data': {
            'successful_uploads': results,
            'failed_uploads': errors,
            'total_files': len(files),
            'successful_count': len(results),
            'failed_count': len(errors)
        }
    })

@app.route('/health')
def health_check():
    """Endpoint per verificare lo stato dell'API"""
    try:
        config_valid = validate_config()
        
        if not config_valid:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Configurazione non valida'
            }), 500
        
        # Verifica la connessione alla blockchain
        blockchain.update_node()
        
        return jsonify({
            'status': 'healthy',
            'username': STEEM_USERNAME,
            'steem_node': getattr(blockchain, 'steem_node', 'unknown'),
            'configuration': 'valid'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Gestisce file troppo grandi"""
    return jsonify({
        'success': False,
        'error': f'File troppo grande. Dimensione massima: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413

if __name__ == '__main__':
    print("🚀 Avvio del server Steem Image Upload API (Flask)")
    print("=" * 60)
    print(f"📝 Username: {STEEM_USERNAME}")
    print(f"🔑 WIF configurato: {'✅ Sì' if validate_config() else '❌ No - controlla il file .env'}")
    print(f"🌐 Server: http://{API_HOST}:{API_PORT}")
    print(f"📊 Endpoints disponibili:")
    print(f"   - GET  /         - Info API")
    print(f"   - POST /upload   - Upload singola immagine")
    print(f"   - POST /upload-multiple - Upload multiple immagini")
    print(f"   - GET  /health   - Stato del servizio")
    print("=" * 60)
    
    if not validate_config():
        print("⚠️  ATTENZIONE: Configurazione non valida!")
        print("💡 Configura STEEM_USERNAME e STEEM_WIF nel file .env")
        print()
    
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=True
    )