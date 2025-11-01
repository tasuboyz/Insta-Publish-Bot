# Quick Start Guide - Instagram Publisher Bot

## ✅ Progetto Ricreato con aiogram!

Il progetto è stato completamente rifatto utilizzando **aiogram 3.x**, il framework moderno per bot Telegram.

### 🎯 Cosa è cambiato?

| Prima (Flask API) | Ora (aiogram Bot) |
|-------------------|-------------------|
| API REST con endpoints | Bot Telegram interattivo |
| Polling/richieste HTTP | Webhook o Polling nativo |
| Integrazione via n8n/cURL | Invii foto direttamente al bot |
| Gestione manuale workflow | Workflow automatico interno |

### 🚀 Avvio Rapido (3 passi)

#### 1️⃣ Configura .env

```powershell
# Copia template
Copy-Item .env.example .env

# Apri e compila con i tuoi dati
notepad .env
```

**Dati richiesti:**
- `TELEGRAM_BOT_TOKEN` - Da [@BotFather](https://t.me/BotFather)
- `STEEM_USERNAME` e `STEEM_WIF` - Account Steem
- `INSTAGRAM_ACCESS_TOKEN` e `INSTAGRAM_ACCOUNT_ID` - Da Facebook Developers

#### 2️⃣ Testa configurazione

```powershell
# Verifica che tutto sia configurato correttamente
python test_config.py
```

Output atteso:
```
✅ Configurazione valida
✅ Connesso a Steem
✅ Connesso a Instagram
✅ Tutti i test passati!
```

#### 3️⃣ Avvia bot

```powershell
# Modalità facile (script automatico)
.\start_bot.ps1

# Oppure manualmente
python bot.py
```

### 💬 Usa il Bot

1. Trova il tuo bot su Telegram
2. Invia `/start`
3. Invia una foto con caption
4. Attendi ~20 secondi
5. Ricevi conferma pubblicazione!

### 📁 Nuova Struttura

```
Image-upload/
├── bot.py                    # 🎯 Entry point (avvia questo!)
├── config.py                 # ⚙️ Configurazione centralizzata
├── requirements.txt          # 📦 Dipendenze aggiornate (aiogram)
├── .env.example             # 📝 Template configurazione
│
├── handlers/                 # 🎮 Handler bot
│   ├── commands.py          # Comandi: /start, /help, /status
│   └── photo_handler.py     # Handler foto (workflow completo)
│
└── services/                 # 🔧 Servizi
    ├── steem_uploader.py    # Upload Steem (async)
    └── instagram_publisher_async.py  # Instagram API (async)
```

### 🔄 Workflow Automatico

Quando invii una foto al bot:

```
📸 Foto ricevuta
   ↓
📥 Download da Telegram
   ↓
⬆️  Upload su Steem blockchain
   ↓
✅ URL pubblico ottenuto
   ↓
📸 Creazione container Instagram
   ↓
⏳ Attesa processing (10s)
   ↓
🎉 Pubblicazione su Instagram
   ↓
💬 Notifica con conferma
```

Tutto automatico, nessuna configurazione n8n richiesta!

### 🆚 Confronto con Versione Precedente

#### Prima (API Flask + n8n)
```
n8n Telegram Trigger
   ↓
HTTP Request → /upload-telegram
   ↓  
HTTP Request → /publish-instagram
   ↓
Telegram Reply
```

#### Ora (Bot aiogram)
```
Bot riceve foto
   ↓
Handler automatico fa tutto
   ↓
Bot risponde con conferma
```

### ⚙️ Modalità Disponibili

#### Polling (Sviluppo)
```env
USE_WEBHOOK=false
```
- ✅ Funziona ovunque (anche localhost)
- ✅ Nessun dominio pubblico richiesto
- ⚠️ Bot deve essere sempre attivo

#### Webhook (Produzione)
```env
USE_WEBHOOK=true
WEBHOOK_URL=https://your-domain.com
```
- ✅ Più efficiente
- ✅ Server risponde solo alle richieste
- ⚠️ Richiede dominio pubblico con HTTPS

### 🧪 Test Singoli Componenti

```powershell
# Test Steem
python services/steem_uploader.py

# Test Instagram
python services/instagram_publisher_async.py

# Test completo
python test_config.py
```

### 📚 Documentazione Completa

- **README.md** - Guida completa setup e troubleshooting
- **INSTAGRAM_API_GUIDE.md** - Guida Instagram API (legacy Flask)
- **IMAGE_UPLOAD_GUIDE.md** - Guida upload Steem (legacy)

### 🎓 Comandi Bot Disponibili

- `/start` - Benvenuto e istruzioni
- `/help` - Guida dettagliata
- `/status` - Verifica stato servizi (Steem + Instagram)
- `/settings` - Mostra configurazione corrente

### 🐛 Problemi Comuni

**"Bot non risponde"**
```powershell
# Verifica token
python -c "from config import config; print(config.bot.token)"

# Test configurazione
python test_config.py
```

**"Errore Steem"**
```powershell
# Test connessione
python services/steem_uploader.py
```

**"Errore Instagram"**
```powershell
# Verifica token
python services/instagram_publisher_async.py
```

### 💡 Vantaggi Nuova Architettura

✅ **Più semplice**: Niente API REST da gestire
✅ **Più veloce**: Workflow completamente async
✅ **Niente n8n**: Tutto gestito internamente
✅ **Più robusto**: aiogram è il framework ufficiale consigliato
✅ **Migliore UX**: Interfaccia conversazionale naturale
✅ **Auto-scaling**: Webhook supporta carico elevato

### 🔧 Prossimi Passi

1. ✅ Installa dipendenze (fatto!)
2. ⚠️ Configura `.env` con i tuoi token
3. ⚠️ Esegui `python test_config.py`
4. ⚠️ Avvia bot con `python bot.py`
5. ⚠️ Testa inviando foto al bot

### 📖 Risorse

- [aiogram Docs](https://docs.aiogram.dev/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Steem Blockchain](https://steem.com/)

---

**Hai domande?** Controlla README.md o chiedi! 🚀
