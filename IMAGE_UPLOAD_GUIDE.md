# Steem Image Upload - Guida all'uso

Questo progetto fornisce diversi modi per caricare immagini su Steem blockchain utilizzando la libreria `beem`.

## 📁 File creati

### 1. `.env` - File di configurazione
Contiene le credenziali Steem per l'upload delle immagini.

### 2. `steem_image_uploader.py` - Classe Python semplice
Esempio di utilizzo diretto della funzione `steem_upload_image` per caricare immagini.

### 3. `flask_image_api.py` - API REST con Flask
Server API per caricare immagini tramite endpoint HTTP.

### 4. `image_upload_api.py` - API REST con FastAPI (avanzata)
Versione più avanzata con FastAPI (richiede dipendenze aggiuntive).

### 5. `test_api_client.py` - Client di test
Script per testare l'API di upload.

## 🚀 Setup iniziale

### 1. Configura le credenziali
Modifica il file `.env`:
```env
STEEM_USERNAME=il_tuo_username_steem
STEEM_WIF=la_tua_chiave_privata_posting
```

⚠️ **IMPORTANTE**: Non condividere mai la tua chiave privata (WIF)!

### 2. Installa le dipendenze base
Le dipendenze principali sono già installate (beem è nel requirements.txt).

Per l'API Flask (opzionale):
```bash
pip install flask python-dotenv
```

Per l'API FastAPI (opzionale):
```bash
pip install fastapi uvicorn python-multipart python-dotenv
```

Per il client di test (opzionale):
```bash
pip install requests
```

## 📖 Modi di utilizzo

### Metodo 1: Utilizzo diretto (semplice)

```python
from steem_image_uploader import SteemImageUploader

# Inizializza l'uploader (usa credenziali dal .env)
uploader = SteemImageUploader()

# Carica una singola immagine
result = uploader.upload_image("percorso/alla/immagine.jpg")

if result["success"]:
    print(f"URL dell'immagine: {result['result']}")
else:
    print(f"Errore: {result['error']}")

# Carica multiple immagini
files = ["immagine1.jpg", "immagine2.png", "immagine3.gif"]
results = uploader.upload_multiple_images(files)
```

### Metodo 2: API REST con Flask

#### Avvio del server:
```bash
python flask_image_api.py
```

Il server sarà disponibile su: http://127.0.0.1:5000

#### Endpoints disponibili:

- **GET /** - Informazioni API
- **POST /upload** - Upload singola immagine
- **POST /upload-multiple** - Upload multiple immagini  
- **GET /health** - Stato del servizio

#### Esempio di utilizzo con curl:

```bash
# Upload singola immagine
curl -X POST -F "file=@immagine.jpg" http://127.0.0.1:5000/upload

# Informazioni API
curl http://127.0.0.1:5000/

# Stato del servizio
curl http://127.0.0.1:5000/health
```

#### Esempio di utilizzo con Python requests:

```python
import requests

# Upload singola immagine
with open('immagine.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://127.0.0.1:5000/upload', files=files)
    print(response.json())

# Upload multiple immagini
files = [
    ('files', open('immagine1.jpg', 'rb')),
    ('files', open('immagine2.png', 'rb'))
]
response = requests.post('http://127.0.0.1:5000/upload-multiple', files=files)
print(response.json())
```

### Metodo 3: Test automatico

Esegui il client di test per verificare che tutto funzioni:

```bash
python test_api_client.py
```

Questo script:
1. Controlla lo stato dell'API
2. Cerca file immagine nella directory corrente
3. Testa l'upload singolo e multiplo
4. Mostra i risultati in formato leggibile

## 📋 Formati supportati

- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)  
- **GIF** (.gif)
- **BMP** (.bmp)
- **WebP** (.webp)

## 📏 Limitazioni

- **Dimensione massima file**: 10MB
- **Upload multipli**: Massimo 10 file per volta
- **Formati**: Solo immagini supportate

## 🔧 Risoluzione problemi

### Errore "Configurazione non valida"
- Controlla che `STEEM_USERNAME` e `STEEM_WIF` siano configurati nel file `.env`
- Assicurati che la chiave WIF sia quella corretta per il posting

### Errore "Posting key Invalid"
- Verifica che la chiave WIF sia corretta
- Assicurati che sia la chiave di posting, non quella attiva o del proprietario

### Errore di connessione al nodo Steem
- La funzione `update_node()` trova automaticamente il nodo più veloce
- Se persiste, potrebbe essere un problema temporaneo della rete Steem

### API non risponde
- Assicurati che il server sia avviato
- Controlla che la porta 5000 non sia occupata da altri servizi
- Verifica le credenziali nel file `.env`

## 💡 Suggerimenti per l'uso

### Per sviluppatori:
1. Usa il **metodo diretto** per script semplici o integrazioni esistenti
2. Usa l'**API Flask** per applicazioni web o servizi REST
3. Usa il **client di test** per verificare il funzionamento

### Per utenti finali:
1. Configura il file `.env` una sola volta
2. Usa `steem_image_uploader.py` come script standalone
3. Modifica i percorsi dei file negli esempi per i tuoi file

### Sicurezza:
- Non mettere mai la chiave WIF nel codice
- Usa sempre il file `.env` per le credenziali
- Aggiungi `.env` al `.gitignore` se usi git

## 📞 Esempio di integrazione

Ecco come integrare l'upload immagini in un bot esistente:

```python
from steem_image_uploader import SteemImageUploader
import os

class BotWithImageUpload:
    def __init__(self):
        self.image_uploader = SteemImageUploader()
    
    def process_image_message(self, file_path):
        """Processa un messaggio con immagine"""
        try:
            # Carica l'immagine su Steem
            result = self.image_uploader.upload_image(file_path)
            
            if result["success"]:
                # Ottiene l'URL dell'immagine
                image_url = result["result"]
                
                # Usa l'URL per creare un post o risposta
                return f"![Immagine]({image_url})"
            else:
                return f"❌ Errore upload: {result['error']}"
                
        except Exception as e:
            return f"❌ Errore: {e}"
        finally:
            # Pulisce il file temporaneo se necessario
            if os.path.exists(file_path):
                os.unlink(file_path)
```

## 🎯 Prossimi passi

1. **Testa con una piccola immagine** per verificare che tutto funzioni
2. **Integra nel tuo progetto** il metodo più adatto alle tue esigenze  
3. **Monitora i log** per eventuali errori durante l'upload
4. **Considera l'uso dell'API** se hai bisogno di caricare immagini da applicazioni esterne

Buon upload! 🚀