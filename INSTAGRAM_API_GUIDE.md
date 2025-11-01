# 📸 Guida Instagram Publishing API

Questa guida spiega come usare i nuovi endpoint per pubblicare su Instagram e il workflow completo che replica il tuo n8n internamente.

## 🎯 Panoramica

Il progetto ora include:
- ✅ **Modulo Instagram Publisher** (`services/instagram_publisher.py`)
- ✅ **Modulo Telegram Handler** (`services/telegram_handler.py`)
- ✅ **Endpoint `/publish-instagram`** - Pubblica direttamente su Instagram
- ✅ **Endpoint `/workflow/telegram-to-instagram`** - Workflow completo automatico

## 📋 Prerequisiti Instagram

### 1. Crea Facebook App
1. Vai su [Facebook Developers](https://developers.facebook.com/)
2. Crea nuova app → Tipo: "Business"
3. Aggiungi prodotto "Instagram Basic Display" o "Instagram Graph API"

### 2. Ottieni Access Token
1. Nel Graph API Explorer: [https://developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/)
2. Seleziona la tua app
3. Richiedi permessi:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. Genera token
5. **Importante**: Estendi il token per renderlo long-lived (60 giorni)

### 3. Ottieni Instagram Account ID
Metodo 1 - Graph API Explorer:
```bash
GET /me/accounts
# Trova la tua Page ID

GET /{page-id}?fields=instagram_business_account
# Ottieni l'Instagram Business Account ID
```

Metodo 2 - cURL:
```bash
curl "https://graph.facebook.com/v23.0/me/accounts?access_token=YOUR_TOKEN"
curl "https://graph.facebook.com/v23.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
```

### 4. Configura .env
```env
# Instagram Configuration
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
INSTAGRAM_ACCOUNT_ID=17841465903297752
FACEBOOK_GRAPH_API_VERSION=v23.0
```

## 🚀 Nuovi Endpoint API

### 1. POST `/publish-instagram` - Pubblica su Instagram

Pubblica un'immagine su Instagram fornendo URL pubblico.

**Request:**
```bash
curl -X POST http://127.0.0.1:5000/publish-instagram \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://images.hive.blog/DQm...",
    "caption": "La mia foto pubblicata da API! #python #instagram"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Pubblicato su Instagram con successo",
  "data": {
    "success": true,
    "container_id": "17980000000000000",
    "media_id": "17980000000000001",
    "image_url": "https://images.hive.blog/DQm...",
    "caption": "La mia foto...",
    "published_at": "2024-11-01T10:30:00",
    "instagram_url": "https://www.instagram.com/p/ABC123/"
  }
}
```

**Da n8n:**
- Nodo: HTTP Request
- Method: POST
- URL: `http://your-server:5000/publish-instagram`
- Body: JSON con `image_url` e `caption`

### 2. POST `/workflow/telegram-to-instagram` - Workflow Completo

Esegue l'intero workflow: Telegram → Steem → Instagram → Reply

**Request:**
```bash
curl -X POST http://127.0.0.1:5000/workflow/telegram-to-instagram \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "AgACAgQAAxkBAAIBd2kFxBixZAFAzOVKOwdrXbR9HQyOAAL3DGsbW_IpUMDZBN1ZAvCsAQADAgADeQADNgQ",
    "caption": "Caption del post",
    "chat_id": "123456789"
  }'
```

**Response:**
```json
{
  "success": true,
  "image_url": "https://images.hive.blog/DQm...",
  "instagram_media_id": "17980000000000001",
  "steps": [
    {
      "step": 1,
      "name": "telegram_download",
      "success": true,
      "file": "file_48.jpg"
    },
    {
      "step": 2,
      "name": "steem_upload",
      "success": true,
      "url": "https://images.hive.blog/DQm..."
    },
    {
      "step": 3,
      "name": "instagram_publish",
      "success": true,
      "media_id": "17980000000000001"
    },
    {
      "step": 4,
      "name": "telegram_reply",
      "success": true
    }
  ]
}
```

**Parametri:**
- `file_id` (required): File ID da Telegram
- `caption` (optional): Didascalia del post Instagram
- `chat_id` (optional): Per inviare conferma su Telegram

## 🔧 Uso Moduli Python

### Instagram Publisher

```python
from services.instagram_publisher import InstagramPublisher

# Inizializza
publisher = InstagramPublisher(
    access_token="EAAxxxxx...",
    instagram_account_id="17841465903297752"
)

# Info account
info = publisher.get_account_info()
print(f"Account: @{info['username']}")

# Pubblica foto
result = publisher.publish_photo(
    image_url="https://example.com/image.jpg",
    caption="Test post da Python! #api"
)

if result['success']:
    print(f"✅ Pubblicato! Media ID: {result['media_id']}")
else:
    print(f"❌ Errore: {result['error']}")
```

### Telegram Handler

```python
from services.telegram_handler import TelegramHandler

# Inizializza
handler = TelegramHandler(bot_token="123456:ABC...")

# Info bot
bot_info = handler.get_me()
print(f"Bot: @{bot_info['username']}")

# Invia messaggio
handler.send_message(
    chat_id=123456789,
    text="Ciao da Python!"
)

# Processa update webhook
update = {...}  # Update da Telegram webhook
data = handler.process_webhook_update(update)
print(f"File ID: {data['file_id']}")
print(f"Caption: {data['caption']}")
```

## 🔄 Migrazione da n8n

### Opzione 1: n8n chiama nuovo endpoint workflow

Sostituisci i nodi n8n con un singolo HTTP Request:

```
Telegram Trigger 
  ↓
Edit Fields (estrai file_id, caption, chat_id)
  ↓
HTTP Request → POST /workflow/telegram-to-instagram
  ↓
(Fine - tutto gestito internamente)
```

Configurazione nodo HTTP Request:
- Method: POST
- URL: `http://your-server:5000/workflow/telegram-to-instagram`
- Body: JSON
  ```json
  {
    "file_id": "{{ $json.message.photo[3].file_id }}",
    "caption": "{{ $json.message.caption }}",
    "chat_id": "{{ $json.message.from.id }}"
  }
  ```

### Opzione 2: Usa endpoint separati (più controllo)

```
Telegram Trigger
  ↓
HTTP Request → POST /upload-telegram (ottieni URL Steem)
  ↓
HTTP Request → POST /publish-instagram (pubblica)
  ↓
Telegram → Send Message (conferma)
```

### Opzione 3: Gestione 100% interna (no n8n)

Crea webhook Flask per ricevere update Telegram direttamente:

```python
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    # Processa con TelegramHandler
    handler = TelegramHandler()
    data = handler.process_webhook_update(update)
    
    if data['has_photo']:
        # Esegui workflow automaticamente
        result = workflow_telegram_to_instagram_internal(
            file_id=data['file_id'],
            caption=data['caption'],
            chat_id=data['chat_id']
        )
    
    return jsonify({'ok': True})
```

Poi configura webhook Telegram:
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -d "url=https://your-server.com/telegram-webhook"
```

## 🧪 Testing

### 1. Test modulo Instagram
```bash
cd services
python instagram_publisher.py
```

### 2. Test modulo Telegram
```bash
cd services
python telegram_handler.py
```

### 3. Test endpoint Instagram
```bash
# Prima avvia server
python main.py

# Poi testa
curl -X POST http://127.0.0.1:5000/publish-instagram \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://picsum.photos/800/600.jpg","caption":"Test API"}'
```

### 4. Test workflow completo
```bash
curl -X POST http://127.0.0.1:5000/workflow/telegram-to-instagram \
  -H "Content-Type: application/json" \
  -d '{
    "file_id":"AgACAgQAAxkBAAIBd2kFxBixZAFAzOVKOwdrXbR9HQyOAAL3DGsbW_IpUMDZBN1ZAvCsAQADAgADeQADNgQ",
    "caption":"Test workflow completo",
    "chat_id":"YOUR_CHAT_ID"
  }'
```

## ⚠️ Limitazioni e Note

### Instagram API
- **Rate limits**: ~200 richieste/ora per app
- **Dimensione immagini**: Min 320px, rapporto 4:5 o 1.91:1
- **Caption**: Max 2200 caratteri
- **Container processing**: Richiede 5-30 secondi prima di publish
- **Account tipo**: Solo Instagram Business o Creator accounts

### Requisiti immagine
- Formato: JPG, PNG
- URL: Deve essere pubblicamente accessibile (HTTPS)
- Dimensioni: Min 320px lato corto
- Rapporto aspetto: 0.8 (4:5) to 1.91:1

### Token Access
- Token standard: 1 ora
- Token long-lived: 60 giorni
- Rinnova prima della scadenza con Graph API

## 🔐 Sicurezza

1. **Mai committare token**: Usa `.env` e `.gitignore`
2. **HTTPS obbligatorio**: Per webhook production
3. **Validazione input**: Gli endpoint validano tutti i parametri
4. **Rate limiting**: Considera implementare limiti richieste
5. **Token rotation**: Rinnova token Instagram regolarmente

## 📚 Risorse

- [Instagram Graph API Docs](https://developers.facebook.com/docs/instagram-api)
- [Content Publishing Guide](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 🆘 Troubleshooting

### "Instagram non configurato"
- Verifica `INSTAGRAM_ACCESS_TOKEN` e `INSTAGRAM_ACCOUNT_ID` in `.env`
- Controlla che il token sia valido con Graph API Explorer

### "Container creation failed"
- Verifica che l'immagine sia accessibile pubblicamente (HTTPS)
- Controlla dimensioni e formato immagine
- Assicurati che l'account Instagram sia Business/Creator

### "Publishing failed"
- Attendi 5-10 secondi tra container creation e publish
- Verifica i permessi del token
- Controlla rate limits dell'app

### "Webhook non riceve update"
- Verifica URL webhook pubblico (usa ngrok per test locale)
- Controlla che il certificato SSL sia valido
- Testa con `getWebhookInfo` API Telegram

---

**Made with ❤️ for automated Instagram publishing**
