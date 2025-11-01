"""
Test script per verificare se un file_id di Telegram è scaricabile
"""

import os
import requests
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configurazione
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FILE_ID = "AgACAgQAAxkBAAIBd2kFxBixZAFAzOVKOwdrXbR9HQyOAAL3DGsbW_IpUMDZBN1ZAvCsAQADAgADeQADNgQ"

def test_telegram_file():
    """Test se il file_id è accessibile su Telegram"""

    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN non configurato nel file .env")
        return False

    print(f"🤖 Test file_id: {FILE_ID}")
    print(f"🔑 Bot token configurato: {'✅ Sì' if TELEGRAM_BOT_TOKEN else '❌ No'}")

    try:
        # URL per ottenere informazioni del file
        base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        get_file_url = f"{base_url}/getFile"

        print("📡 Richiesta informazioni file...")

        # Ottieni informazioni del file
        response = requests.get(get_file_url, params={"file_id": FILE_ID}, timeout=10)
        response.raise_for_status()

        data = response.json()
        print(f"📄 Risposta API: {data}")

        if not data.get("ok"):
            print(f"❌ Errore API Telegram: {data.get('description', 'Unknown error')}")
            return False

        file_data = data["result"]
        file_path = file_data["file_path"]
        file_size = file_data.get("file_size", 0)

        print("✅ File trovato su Telegram!")
        print(f"   📁 Path: {file_path}")
        print(f"   📏 Dimensione: {file_size:,} bytes")

        # Verifica se è un'immagine
        file_extension = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

        if file_extension in image_extensions:
            print(f"   🖼️  Tipo: Immagine ({file_extension.upper()})")
        else:
            print(f"   ❓ Tipo: {file_extension} (potrebbe non essere un'immagine)")

        # Test download (solo headers, non scaricare tutto il file)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        print("\n📥 Test download...")
        download_response = requests.head(file_url, timeout=10)

        if download_response.status_code == 200:
            print("✅ File scaricabile!")
            content_length = download_response.headers.get('content-length')
            if content_length:
                print(f"   📏 Content-Length: {int(content_length):,} bytes")
        else:
            print(f"❌ Errore download: HTTP {download_response.status_code}")
            return False

        print("\n🎉 File_id VALIDO e SCARICABILE!")
        return True

    except requests.exceptions.Timeout:
        print("⏰ Timeout nella richiesta a Telegram")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 Errore di connessione: {e}")
        return False
    except Exception as e:
        print(f"💥 Errore imprevisto: {e}")
        return False

    except requests.exceptions.Timeout:
        print("⏰ Timeout nella richiesta a Telegram")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 Errore di connessione: {e}")
        return False
    except Exception as e:
        print(f"💥 Errore imprevisto: {e}")
        return False

def test_full_download():
    """Test completo download (opzionale, scarica effettivamente il file)"""
    if not TELEGRAM_BOT_TOKEN:
        return

    try:
        print("\n🔄 Test download completo...")

        base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

        # Ottieni info file
        response = requests.get(f"{base_url}/getFile", params={"file_id": FILE_ID})
        file_data = response.json()["result"]
        file_path = file_data["file_path"]

        # Scarica file
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        download_response = requests.get(file_url)

        if download_response.status_code == 200:
            # Salva temporaneamente per test
            temp_filename = f"test_telegram_{FILE_ID[:10]}.jpg"
            with open(temp_filename, 'wb') as f:
                f.write(download_response.content)

            file_size = len(download_response.content)
            print(f"✅ Download completato: {temp_filename} ({file_size:,} bytes)")

            # Verifica che sia un'immagine valida
            try:
                from PIL import Image
                with Image.open(temp_filename) as img:
                    img.verify()
                print("✅ File è un'immagine valida!")
            except Exception as e:
                print(f"⚠️  File potrebbe non essere un'immagine valida: {e}")

            # Pulisci
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
                print("🧹 File temporaneo eliminato")

        else:
            print(f"❌ Errore download: HTTP {download_response.status_code}")

    except Exception as e:
        print(f"❌ Errore download completo: {e}")

if __name__ == "__main__":
    print("🧪 Test File ID Telegram")
    print("=" * 50)

    # Test base
    success = test_telegram_file()

    if success:
        # Opzionale: test download completo
        choice = input("\nVuoi testare anche il download completo? (y/N): ").lower().strip()
        if choice == 'y':
            test_full_download()

    print("\n" + "=" * 50)
    if success:
        print("✅ File_id VALIDO - Puoi usarlo con l'API!")
        print("💡 Esempio chiamata API:")
        print(f'   curl -X POST http://127.0.0.1:5000/upload-telegram \\')
        print(f'        -H "Content-Type: application/json" \\')
        print(f'        -d \'{{"file_id": "{FILE_ID}"}}\'')
    else:
        print("❌ File_id NON valido o non accessibile")