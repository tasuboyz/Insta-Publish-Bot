# 🤖 Instagram Publisher Bot - Telegram

Bot Telegram che pubblica automaticamente le foto su Instagram usando aiogram 3.x, Steem blockchain e Facebook Graph API.

## ✨ Caratteristiche

- 📸 **Pubblicazione automatica**: Invia foto nel bot → Pubblicata su Instagram
- 🔗 **Upload blockchain**: Immagini caricate su Steem prima della pubblicazione
- ⏰ **Programmazione post**: Pianifica pubblicazioni future con calendario interattivo
- 📅 **Calendario inline**: Seleziona data e ora con tastiere inline
- 🌐 **Webhook & Polling**: Supporta entrambe le modalità
- ⚡️ **Async**: Completamente asincrono con aiogram 3.x
- 🎯 **Comandi**: /start, /help, /status, /settings, /schedule, /scheduled

## 🏗 Architettura

```
bot.py                          # Entry point principale
├── config.py                   # Configurazione centralizzata
├── handlers/
│   ├── commands.py            # Handler comandi (/start, /help, etc.)
│   ├── photo_handler.py       # Handler foto e documenti
│   └── calendar.py            # Handler calendario e programmazione
├── services/
│   ├── steem_uploader.py      # Upload immagini su Steem
│   ├── instagram_publisher_async.py  # Pubblicazione Instagram
│   ├── scheduler.py           # Gestione post programmati
│   └── token_manager.py       # Gestione token Instagram
└── scheduled_posts.json       # Storage post programmati
```

### Workflow

```
User invia foto
    ↓
Handler photo_handler.py
    ↓
1. Download da Telegram
    ↓
2. Upload su Steem → URL pubblico
    ↓
3. Crea container Instagram
    ↓
4. Attende processing (10s)
    ↓
5. Pubblica su Instagram
    ↓
6. Reply con link e conferma
```

## 📦 Installazione

### 1. Clona e installa dipendenze

```powershell
# Clona repository
git clone <your-repo>
cd Image-upload

# Crea virtual environment (opzionale ma consigliato)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Configura variabili d'ambiente

Copia `.env.example` in `.env`:

```powershell
Copy-Item .env.example .env
```

Compila `.env` con i tuoi dati:

```env
# Bot Telegram (ottieni da @BotFather)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Modalità: polling per sviluppo, webhook per produzione
USE_WEBHOOK=false

# Steem (per upload immagini)
STEEM_USERNAME=your-username
STEEM_WIF=5KYourPrivatePostingKey...

# Instagram (da Facebook Developers)
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
INSTAGRAM_ACCOUNT_ID=17841465903297752
```

### 3. Ottieni credenziali

#### Telegram Bot Token
1. Apri [@BotFather](https://t.me/BotFather) su Telegram
2. Invia `/newbot`
3. Segui le istruzioni
4. Copia il token

#### Instagram Access Token
1. Crea app su [Facebook Developers](https://developers.facebook.com/)
2. Aggiungi prodotto "Instagram Graph API"
3. Richiedi permessi: `instagram_basic`, `instagram_content_publish`
4. Usa [Graph API Explorer](https://developers.facebook.com/tools/explorer/) per generare token
5. Estendi token a long-lived (60 giorni)
6. Ottieni Instagram Business Account ID:
   ```bash
   curl "https://graph.facebook.com/v23.0/me/accounts?access_token=YOUR_TOKEN"
   curl "https://graph.facebook.com/v23.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN"
   ```

#### Steem Keys
1. Accedi al tuo account Steem
2. Vai su Wallet → Permissions
3. Copia la **Posting Key** (formato WIF: inizia con `5K`)

## 🚀 Utilizzo

### Modalità Polling (Sviluppo locale)

```powershell
# Configura .env
USE_WEBHOOK=false

# Avvia bot
python bot.py
```

### Modalità Webhook (Produzione)

```powershell
# Configura .env
USE_WEBHOOK=true
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
WEB_APP_HOST=0.0.0.0
WEB_APP_PORT=8080

# Avvia bot
python bot.py
```

**Nota**: Per webhook serve dominio pubblico con HTTPS. Per test locale usa [ngrok](https://ngrok.com/):

```powershell
# In un altro terminale
ngrok http 8080

# Copia URL HTTPS e mettilo in WEBHOOK_URL
WEBHOOK_URL=https://abc123.ngrok.io
```

## ⏰ Programmazione Post

Il bot supporta la programmazione di post per date e orari futuri.

### Come programmare un post

1. **Seleziona data e ora**:
   ```
   /schedule
   ```
   - Usa il calendario inline per selezionare la data
   - Scegli ora e minuti con i pulsanti

2. **Invia la foto**:
   - Dopo aver selezionato data/ora, invia la foto
   - Aggiungi caption se desiderato
   - Il post sarà programmato automaticamente

3. **Gestisci post programmati**:
   ```
   /scheduled
   ```
   - Visualizza tutti i post programmati
   - Stato: ⏰ programmato, ✅ pubblicato, ❌ fallito, 🚫 cancellato

### Come funziona

- **Calendario interattivo**: Naviga mesi con ◀️ ▶️
- **Date future**: Puoi programmare solo per date future
- **Pubblicazione automatica**: Task in background controlla ogni minuto
- **Storage**: Post salvati in `scheduled_posts.json`
- **Notifiche**: Ricevi aggiornamenti quando il post viene pubblicato

### Esempio workflow

```
/schedule
[seleziona data 15/12/2025]
[seleziona ora 14:30]
[invia foto con caption]
→ Post programmato per 15/12/2025 14:30
```

## 🔑 Gestione Token Instagram

Il bot include gestione automatica dei token Instagram per evitare scadenze.

### Controllo Stato Token

Usa `/status` per vedere:
- ✅ Stato connessione Instagram
- 🔑 Scadenza token (giorni/ore rimanenti)
- 📊 Followers e numero post

### Aggiornamento Automatico

- **Background task**: Controlla giornalmente la scadenza
- **Auto-refresh**: Rinnova token 7 giorni prima della scadenza
- **Persistenza**: Salva nuovi token nel file `.env`

### Aggiornamento Manuale

Se il token è scaduto o hai problemi:

```
/refresh_token
```

Questo forza l'aggiornamento immediato del token.

### Risoluzione Problemi Token

**Token scaduto:**
```
/refresh_token
```
Oppure genera un nuovo token su [Facebook Developers](https://developers.facebook.com/tools/explorer/)

**Errore 400 Bad Request:**
- Token Instagram non valido
- Credenziali Facebook App errate
- Permessi insufficienti

**Controllo validità:**
```bash
python -c "from services.token_manager import debug_token; import asyncio; asyncio.run(debug_token('YOUR_TOKEN'))"
```

## 💬 Comandi Bot

- `/start` - Messaggio di benvenuto
- `/help` - Guida completa
- `/status` - Stato servizi e token Instagram
- `/settings` - Impostazioni bot
- `/schedule` - Programma un post futuro
- `/scheduled` - Gestisci post programmati
- `/refresh_token` - Forza aggiornamento token Instagram
- `/generate_token` - Genera nuovo token Instagram via OAuth

## 📸 Inviare Foto

1. Apri chat con il bot
2. Invia una foto (compressa o documento)
3. Aggiungi caption (opzionale)
4. Attendi pubblicazione (~15-30s)
5. Ricevi link post Instagram

### Formati supportati
- **Tipi**: JPG, JPEG, PNG
- **Dimensione max**: 20 MB
- **Rapporto aspetto**: 4:5 (verticale) o 1.91:1 (orizzontale)

## 🧪 Testing

### Test configurazione

```powershell
python -c "from config import config; errors = config.validate(); print('✅ OK' if not errors else '\n'.join(errors))"
```

### Test connessione Steem

```powershell
python services/steem_uploader.py
```

### Test connessione Instagram

```powershell
python services/instagram_publisher_async.py
```

### Test bot

```powershell
# Avvia in polling mode
python bot.py

# Invia foto al bot su Telegram
```

## 📁 Struttura File

```
Image-upload/
├── bot.py                    # Entry point
├── config.py                 # Configurazione
├── requirements.txt          # Dipendenze Python
├── .env.example             # Template configurazione
├── .env                     # Configurazione (non committare!)
├── scheduled_posts.json     # Storage post programmati
├── handlers/
│   ├── __init__.py
│   ├── commands.py          # /start, /help, /status
│   ├── photo_handler.py     # Handler foto
│   └── calendar.py          # Handler calendario e programmazione
├── services/
│   ├── __init__.py
│   ├── steem_uploader.py    # Upload Steem
│   ├── instagram_publisher_async.py  # Pubblicazione IG
│   ├── scheduler.py         # Gestione post programmati
│   └── token_manager.py     # Gestione token Instagram
└── temp/                    # File temporanei (auto-creata)
```

## ⚙️ Configurazione Avanzata

### Logging

Modifica `LOG_LEVEL` in `.env`:

```env
LOG_LEVEL=DEBUG   # Per debugging dettagliato
LOG_LEVEL=INFO    # Default
LOG_LEVEL=WARNING # Solo warning ed errori
LOG_LEVEL=ERROR   # Solo errori
```

### Nodi Steem Custom

```env
STEEM_NODES=https://api.steemit.com,https://api.steemdb.com,https://steemd.minnowsupportproject.org
```

Il bot cerca automaticamente il nodo più veloce all'avvio. Puoi disabilitare questa funzionalità:

```env
STEEM_AUTO_FIND_FASTEST=false
```

**Funzionalità Ricerca Automatica:**
- 🔍 All'avvio, il bot testa i nodi disponibili
- ⚡️ Seleziona automaticamente il più veloce
- 📡 Ottiene lista dinamica da `https://steem.senior.workers.dev/`
- 🔄 Usa i nodi configurati come fallback
- ✅ Migliora velocità di upload immagini

### Directory Temporanea

```env
TEMP_DIR=C:\Temp\bot_images
```

## 🐛 Troubleshooting

### Bot non risponde
- Verifica `TELEGRAM_BOT_TOKEN` in `.env`
- Controlla log per errori connessione
- Se webhook: verifica URL pubblico con HTTPS

### Errore upload Steem
- Verifica `STEEM_USERNAME` e `STEEM_WIF`
- Controlla connessione ai nodi: `python services/steem_uploader.py`
- Prova nodi alternativi in `STEEM_NODES`

### Errore Instagram
- Verifica token valido: `python services/instagram_publisher_async.py`
- Controlla permessi app Facebook
- Account Instagram deve essere Business/Creator
- Token scaduto? Usa `/refresh_token` o rinnova su Graph API Explorer

### Token Scaduto
- Usa comando `/refresh_token` nel bot
- Oppure genera nuovo token su Facebook Developers
- Controlla stato con `/status`

### Problemi App Facebook
Se `/refresh_token` fallisce con errore 400:

**Configurazione App Facebook:**
1. Vai su https://developers.facebook.com/apps
2. Seleziona la tua app
3. **Modalità Live**: Assicurati che l'app sia in "Live Mode" (non Development)
4. **Prodotti**: Aggiungi "Instagram Graph API"
5. **Permessi**: Configura permessi appropriati:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
   - `pages_show_list`

**Test Configurazione:**
```bash
python -c "
import asyncio
from services.token_manager import test_facebook_app_config
result = asyncio.run(test_facebook_app_config())
print('Config OK:', result['app_configured'])
print('Can exchange:', result['can_exchange_tokens'])
print('Issues:', result['issues'])
"
```

**Genera Nuovo Token:**
Se l'app è configurata correttamente ma il refresh fallisce:
```
/generate_token
```
Questo avvia il processo OAuth per generare un nuovo token da zero.

### "Container creation failed"
- Immagine deve essere pubblicamente accessibile (HTTPS)
- Verifica dimensioni e rapporto aspetto
- URL Steem deve essere `https://images.steem.blog/...`

### "Publishing failed"
- Attendi 10-15 secondi tra container e publish
- Verifica rate limits Instagram (200 req/ora)
- Controlla che container sia processato

## 📚 Risorse

- [aiogram Documentation](https://docs.aiogram.dev/en/latest/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Steem Blockchain](https://steem.com/)
- [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)

## 🔐 Sicurezza

- ⚠️ **Mai committare `.env`**: Aggiungi a `.gitignore`
- 🔑 **Proteggi WIF key**: È come la password del tuo account Steem
- 🔒 **HTTPS obbligatorio**: Per webhook production
- 🔄 **Token auto-refresh**: Il bot aggiorna automaticamente i token Instagram
- 🛡 **Rate limiting**: Instagram limita a ~200 richieste/ora

## 📄 Licenza

MIT License

## 🙋 Support

Hai problemi? Apri una issue su GitHub o contatta l'admin del bot.

---

**Made with ❤️ using aiogram 3.x**
