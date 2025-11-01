"""
Main API Flask per upload immagini su Steem/Hive blockchain
Supporta:
- Upload diretto di file
- Download da Telegram tramite file_id
- Upload multipli
- Gestione errori completa
- CORS per applicazioni web

Per configurare:
1. Crea file .env con STEEM_USERNAME, STEEM_WIF, TELEGRAM_BOT_TOKEN
2. pip install -r requirements.txt
3. python main.py

Endpoints:
- GET / - Informazioni API
- POST /upload - Upload file diretto
- POST /upload-telegram - Upload da Telegram file_id
- POST /upload-multiple - Upload multipli
- GET /health - Stato servizio
"""

import os
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from PIL import Image
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()

# Importa blockchain (assumendo struttura esistente)
try:
    from utils.steem_request import Blockchain
except ImportError:
    logger.error("❌ Impossibile importare Blockchain. Assicurati che il modulo utils.steem_request esista")
    exit(1)

# Importa servizi modulari
try:
    from services.instagram_publisher import InstagramPublisher
    from services.telegram_handler import TelegramHandler
    INSTAGRAM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Servizi Instagram/Telegram non disponibili: {e}")
    INSTAGRAM_AVAILABLE = False
    InstagramPublisher = None
    TelegramHandler = None

# Configurazione
STEEM_USERNAME = os.getenv("STEEM_USERNAME")
STEEM_WIF = os.getenv("STEEM_WIF") 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG", "True").lower() == "true"

# Configurazione file
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'steem_uploads')

# Crea directory temporanea se non esiste
os.makedirs(TEMP_DIR, exist_ok=True)

# Inizializza Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
CORS(app, origins="*")  # Abilita CORS per tutte le origini

# Inizializza blockchain
try:
    blockchain = Blockchain()
    logger.info("✅ Blockchain inizializzata correttamente")
except Exception as e:
    logger.error(f"❌ Errore inizializzazione blockchain: {e}")
    blockchain = None


class TelegramFileDownloader:
    """Gestisce il download di file da Telegram"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.file_url = f"https://api.telegram.org/file/bot{bot_token}"
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Ottiene informazioni sul file da Telegram"""
        try:
            response = requests.get(f"{self.base_url}/getFile", params={"file_id": file_id})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Errore ottenendo info file {file_id}: {e}")
            raise Exception(f"Impossibile ottenere informazioni file: {e}")
    
    def download_file(self, file_id: str) -> tuple[str, str]:
        """
        Scarica un file da Telegram
        
        Returns:
            tuple: (percorso_file_locale, nome_file_originale)
        """
        try:
            # Ottiene informazioni sul file
            file_info = self.get_file_info(file_id)
            
            if not file_info.get("ok"):
                raise Exception(f"Errore API Telegram: {file_info.get('description', 'Unknown error')}")
            
            file_data = file_info["result"]
            file_path = file_data["file_path"]
            file_size = file_data.get("file_size", 0)
            
            # Controlla dimensione
            if file_size > MAX_FILE_SIZE:
                raise Exception(f"File troppo grande: {file_size} bytes (max: {MAX_FILE_SIZE})")
            
            # Scarica il file
            download_url = f"{self.file_url}/{file_path}"
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Genera nome file temporaneo
            file_extension = Path(file_path).suffix or '.jpg'
            temp_filename = f"telegram_{file_id}_{int(datetime.now().timestamp())}{file_extension}"
            temp_path = os.path.join(TEMP_DIR, temp_filename)
            
            # Salva il file
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            original_filename = Path(file_path).name
            logger.info(f"✅ File scaricato: {original_filename} -> {temp_path}")
            
            return temp_path, original_filename
            
        except Exception as e:
            logger.error(f"Errore download file {file_id}: {e}")
            raise


class ImageUploadService:
    """Servizio principale per l'upload delle immagini"""
    
    def __init__(self):
        self.blockchain = blockchain
        self.username = STEEM_USERNAME
        self.wif = STEEM_WIF
        self.telegram_downloader = TelegramFileDownloader(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
    
    def validate_config(self) -> bool:
        """Verifica configurazione"""
        if not self.username or self.username == "your_username_here":
            return False
        if not self.wif or self.wif == "your_wif_here":
            return False
        if not self.blockchain:
            return False
        return True
    
    def validate_image_file(self, file_path: str) -> bool:
        """Valida se il file è un'immagine valida"""
        try:
            # Controlla estensione
            file_extension = Path(file_path).suffix.lower().lstrip('.')
            if file_extension not in ALLOWED_EXTENSIONS:
                raise Exception(f"Formato non supportato: {file_extension}")
            
            # Verifica che sia un'immagine leggibile
            with Image.open(file_path) as img:
                img.verify()
            
            # Controlla dimensioni
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                raise Exception(f"File troppo grande: {file_size} bytes")
            
            return True
            
        except Exception as e:
            logger.error(f"Validazione fallita per {file_path}: {e}")
            raise Exception(f"File non valido: {e}")
    
    def upload_to_steem(self, file_path: str, cleanup: bool = True) -> Dict[str, Any]:
        """Carica immagine su Steem/Hive"""
        try:
            if not self.validate_config():
                raise Exception("Configurazione non valida - controlla STEEM_USERNAME e STEEM_WIF")
            
            # Valida immagine
            self.validate_image_file(file_path)
            
            # Upload su blockchain
            logger.info(f"📤 Upload {Path(file_path).name} su blockchain...")
            result = self.blockchain.steem_upload_image(file_path, self.username, self.wif)
            
            # Estrae URL dal risultato
            if isinstance(result, dict) and 'url' in result:
                image_url = result['url']
            elif isinstance(result, str):
                image_url = result
            else:
                image_url = str(result)
            
            logger.info(f"✅ Upload completato: {image_url}")
            
            return {
                "success": True,
                "url": image_url,
                "filename": Path(file_path).name,
                "size_bytes": os.path.getsize(file_path),
                "uploaded_by": self.username,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Errore upload {file_path}: {e}")
            raise Exception(f"Upload fallito: {e}")
        
        finally:
            # Pulizia file temporaneo
            if cleanup and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.debug(f"🧹 File temporaneo eliminato: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossibile eliminare file temporaneo {file_path}: {e}")


# Inizializza servizio
upload_service = ImageUploadService()


def allowed_file(filename: str) -> bool:
    """Verifica se il file ha estensione supportata"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    """Endpoint informazioni API"""
    config_valid = upload_service.validate_config()
    
    return jsonify({
        'service': 'Steem/Hive Image Upload API',
        'version': '2.0.0',
        'status': 'running',
        'configuration': 'valid' if config_valid else 'invalid',
        'features': {
            'direct_upload': True,
            'telegram_integration': bool(TELEGRAM_BOT_TOKEN),
            'multiple_upload': True,
            'image_validation': True
        },
        'limits': {
            'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
            'supported_formats': list(ALLOWED_EXTENSIONS),
            'max_multiple_files': 10
        },
        'endpoints': {
            'upload_file': 'POST /upload',
            'upload_telegram': 'POST /upload-telegram',
            'upload_multiple': 'POST /upload-multiple', 
            'health_check': 'GET /health'
        },
        'blockchain': {
            'username': upload_service.username if config_valid else 'not_configured',
            'network': 'steem/hive'
        },
        'telegram': {
            'enabled': bool(TELEGRAM_BOT_TOKEN),
            'bot_configured': bool(TELEGRAM_BOT_TOKEN)
        }
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload diretto di file"""
    try:
        if not upload_service.validate_config():
            return jsonify({
                'success': False,
                'error': 'Servizio non configurato - controlla STEEM_USERNAME e STEEM_WIF'
            }), 500
        
        # Controllo file
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file fornito'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'Formato non supportato. Supportati: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Salva temporaneamente
        filename = secure_filename(file.filename)
        file_extension = Path(filename).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, dir=TEMP_DIR)
        temp_path = temp_file.name
        
        file.save(temp_path)
        
        # Upload
        result = upload_service.upload_to_steem(temp_path)
        
        return jsonify({
            'success': True,
            'message': 'Immagine caricata con successo',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload-telegram', methods=['POST'])
def upload_telegram():
    """Upload da Telegram file_id"""
    try:
        if not upload_service.validate_config():
            return jsonify({
                'success': False,
                'error': 'Servizio non configurato'
            }), 500
        
        if not upload_service.telegram_downloader:
            return jsonify({
                'success': False,
                'error': 'Telegram non configurato - manca TELEGRAM_BOT_TOKEN'
            }), 500
        
        # Ottieni file_id da JSON body, form data o query params (supporta n8n bodyParameters)
        data = request.get_json(silent=True) or {}
        file_id = data.get('file_id') or request.form.get('file_id') or request.args.get('file_id')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id richiesto nel body JSON, form data o query params'
            }), 400
        
        # Scarica da Telegram
        logger.info(f"📥 Download file da Telegram: {file_id}")
        temp_path, original_filename = upload_service.telegram_downloader.download_file(file_id)
        
        # Upload su blockchain
        result = upload_service.upload_to_steem(temp_path)
        result['original_filename'] = original_filename
        result['telegram_file_id'] = file_id
        
        return jsonify({
            'success': True,
            'message': 'Immagine da Telegram caricata con successo',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Errore upload Telegram: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/upload-multiple', methods=['POST'])
def upload_multiple():
    """Upload multipli"""
    try:
        if not upload_service.validate_config():
            return jsonify({
                'success': False,
                'error': 'Servizio non configurato'
            }), 500
        
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'Nessun file fornito'}), 400
        
        if len(files) > 10:
            return jsonify({'success': False, 'error': 'Massimo 10 file per volta'}), 400
        
        results = []
        errors = []
        
        for file in files:
            try:
                if file.filename == '' or not allowed_file(file.filename):
                    errors.append({
                        'filename': file.filename or 'unnamed',
                        'error': 'Nome file vuoto o formato non supportato'
                    })
                    continue
                
                # Salva temporaneamente
                filename = secure_filename(file.filename)
                file_extension = Path(filename).suffix
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, dir=TEMP_DIR)
                temp_path = temp_file.name
                
                file.save(temp_path)
                
                # Upload
                result = upload_service.upload_to_steem(temp_path)
                results.append(result)
                
            except Exception as e:
                errors.append({
                    'filename': file.filename or 'unknown',
                    'error': str(e)
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
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """Controllo stato servizio"""
    try:
        config_valid = upload_service.validate_config()
        
        if not config_valid:
            return jsonify({
                'status': 'unhealthy',
                'error': 'Configurazione non valida',
                'checks': {
                    'config': False,
                    'blockchain': False,
                    'telegram': bool(TELEGRAM_BOT_TOKEN),
                    'instagram': bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)
                }
            }), 500
        
        # Test connessione blockchain
        blockchain.update_node()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'config': True,
                'blockchain': True,
                'telegram': bool(TELEGRAM_BOT_TOKEN),
                'instagram': bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)
            },
            'info': {
                'username': upload_service.username,
                'temp_dir': TEMP_DIR,
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024)
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'checks': {
                'config': upload_service.validate_config(),
                'blockchain': False,
                'telegram': bool(TELEGRAM_BOT_TOKEN),
                'instagram': bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)
            }
        }), 500


@app.route('/publish-instagram', methods=['POST'])
def publish_instagram():
    """Pubblica immagine su Instagram"""
    try:
        if not INSTAGRAM_AVAILABLE or not InstagramPublisher:
            return jsonify({
                'success': False,
                'error': 'Servizio Instagram non disponibile - controlla dipendenze'
            }), 500
        
        if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
            return jsonify({
                'success': False,
                'error': 'Instagram non configurato - manca INSTAGRAM_ACCESS_TOKEN o INSTAGRAM_ACCOUNT_ID'
            }), 500
        
        # Ottieni dati dal request (JSON body, form o query params)
        data = request.get_json(silent=True) or {}
        image_url = data.get('image_url') or request.form.get('image_url') or request.args.get('image_url')
        caption = data.get('caption', '') or request.form.get('caption', '') or request.args.get('caption', '')
        
        if not image_url:
            return jsonify({
                'success': False,
                'error': 'image_url richiesto nel body JSON, form data o query params'
            }), 400
        
        # Inizializza publisher
        publisher = InstagramPublisher(
            access_token=INSTAGRAM_ACCESS_TOKEN,
            instagram_account_id=INSTAGRAM_ACCOUNT_ID
        )
        
        # Pubblica su Instagram
        logger.info(f"📸 Pubblicazione Instagram: {image_url}")
        result = publisher.publish_photo(image_url, caption)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Pubblicato su Instagram con successo',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Errore pubblicazione Instagram')
            }), 500
        
    except Exception as e:
        logger.error(f"Errore publish Instagram: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/workflow/telegram-to-instagram', methods=['POST'])
def workflow_telegram_to_instagram():
    """
    Workflow completo: Telegram → Steem Upload → Instagram Publish
    Replica il workflow n8n internamente
    """
    try:
        # Validazione configurazione
        if not upload_service.validate_config():
            return jsonify({
                'success': False,
                'error': 'Servizio Steem non configurato'
            }), 500
        
        if not INSTAGRAM_AVAILABLE or not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
            return jsonify({
                'success': False,
                'error': 'Servizio Instagram non configurato'
            }), 500
        
        # Ottieni dati input
        data = request.get_json(silent=True) or {}
        file_id = data.get('file_id') or request.form.get('file_id')
        caption = data.get('caption', '') or request.form.get('caption', '')
        chat_id = data.get('chat_id') or request.form.get('chat_id')  # Per rispondere su Telegram
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id richiesto'
            }), 400
        
        workflow_result = {
            'success': False,
            'steps': []
        }
        
        # STEP 1: Download da Telegram
        logger.info(f"🔄 STEP 1: Download file_id {file_id}")
        try:
            temp_path, original_filename = upload_service.telegram_downloader.download_file(file_id)
            workflow_result['steps'].append({
                'step': 1,
                'name': 'telegram_download',
                'success': True,
                'file': original_filename
            })
        except Exception as e:
            workflow_result['steps'].append({
                'step': 1,
                'name': 'telegram_download',
                'success': False,
                'error': str(e)
            })
            return jsonify(workflow_result), 500
        
        # STEP 2: Upload su Steem
        logger.info(f"🔄 STEP 2: Upload su Steem")
        try:
            steem_result = upload_service.upload_to_steem(temp_path)
            image_url = steem_result['url']
            workflow_result['steps'].append({
                'step': 2,
                'name': 'steem_upload',
                'success': True,
                'url': image_url
            })
        except Exception as e:
            workflow_result['steps'].append({
                'step': 2,
                'name': 'steem_upload',
                'success': False,
                'error': str(e)
            })
            return jsonify(workflow_result), 500
        
        # STEP 3: Pubblica su Instagram
        logger.info(f"🔄 STEP 3: Pubblicazione Instagram")
        try:
            publisher = InstagramPublisher(
                access_token=INSTAGRAM_ACCESS_TOKEN,
                instagram_account_id=INSTAGRAM_ACCOUNT_ID
            )
            instagram_result = publisher.publish_photo(image_url, caption)
            
            if instagram_result.get('success'):
                workflow_result['steps'].append({
                    'step': 3,
                    'name': 'instagram_publish',
                    'success': True,
                    'media_id': instagram_result.get('media_id')
                })
            else:
                raise Exception(instagram_result.get('error', 'Errore Instagram'))
                
        except Exception as e:
            workflow_result['steps'].append({
                'step': 3,
                'name': 'instagram_publish',
                'success': False,
                'error': str(e)
            })
            return jsonify(workflow_result), 500
        
        # STEP 4: Rispondi su Telegram (opzionale)
        if chat_id and TELEGRAM_BOT_TOKEN:
            logger.info(f"🔄 STEP 4: Risposta Telegram")
            try:
                telegram_handler = TelegramHandler(TELEGRAM_BOT_TOKEN)
                telegram_handler.send_message(
                    chat_id=int(chat_id),
                    text="✅ Content Posted!\n\n"
                         f"📸 Instagram: Pubblicato\n"
                         f"🔗 Steem: {image_url}"
                )
                workflow_result['steps'].append({
                    'step': 4,
                    'name': 'telegram_reply',
                    'success': True
                })
            except Exception as e:
                workflow_result['steps'].append({
                    'step': 4,
                    'name': 'telegram_reply',
                    'success': False,
                    'error': str(e)
                })
        
        # Risultato finale
        workflow_result['success'] = True
        workflow_result['image_url'] = image_url
        workflow_result['instagram_media_id'] = instagram_result.get('media_id')
        
        return jsonify(workflow_result)
        
    except Exception as e:
        logger.error(f"Errore workflow completo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(413)
def file_too_large(e):
    """Gestisce file troppo grandi"""
    return jsonify({
        'success': False,
        'error': f'File troppo grande. Dimensione massima: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413


@app.errorhandler(500)
def internal_error(e):
    """Gestisce errori interni"""
    return jsonify({
        'success': False,
        'error': 'Errore interno del server'
    }), 500


if __name__ == '__main__':
    print("🚀 Steem/Hive Image Upload API v2.0")
    print("=" * 60)
    print(f"📝 Username: {STEEM_USERNAME or 'NON CONFIGURATO'}")
    print(f"🔑 WIF: {'✅ Configurato' if STEEM_WIF else '❌ Mancante'}")
    print(f"🤖 Telegram: {'✅ Abilitato' if TELEGRAM_BOT_TOKEN else '❌ Non configurato'}")
    print(f"🌐 Server: http://{API_HOST}:{API_PORT}")
    print(f"📁 Directory temp: {TEMP_DIR}")
    print("=" * 60)
    print("📊 Endpoints:")
    print("   GET  /         - Informazioni API")
    print("   POST /upload   - Upload diretto file")
    print("   POST /upload-telegram - Upload da Telegram file_id")
    print("   POST /upload-multiple - Upload multipli")
    print("   GET  /health   - Stato servizio")
    print("=" * 60)
    
    if not upload_service.validate_config():
        print("⚠️  CONFIGURAZIONE INCOMPLETA!")
        print("💡 Configura nel file .env:")
        print("   STEEM_USERNAME=tuo_username")
        print("   STEEM_WIF=tua_chiave_posting")
        print("   TELEGRAM_BOT_TOKEN=token_bot (opzionale)")
        print()
    
    try:
        app.run(
            host=API_HOST,
            port=API_PORT,
            debug=DEBUG_MODE
        )
    except KeyboardInterrupt:
        print("\n👋 Server fermato dall'utente")
    except Exception as e:
        print(f"❌ Errore avvio server: {e}")