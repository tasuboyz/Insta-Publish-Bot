# 🗓 Sistema Post Programmati - Guida Completa

## ✅ Implementazione SQLite

Il sistema di programmazione post ora usa **SQLite** invece di JSON per gestire:
- ✅ Sessioni utente (data/ora selezionate)
- ✅ Post programmati
- ✅ Storico pubblicazioni

## 📁 File del Sistema

```
services/
├── database.py          # Gestore database SQLite
├── scheduler.py         # Scheduler post (usa database.py)
└── ...

handlers/
├── calendar.py          # UI calendario e selezione ora
├── photo_handler.py     # Processing foto + programmazione
└── commands.py          # Comando /scheduled

bot_data.db             # Database SQLite (auto-creato)
```

## 🔄 Workflow Completo

### 1️⃣ Utente Programma Post

```
/schedule
    ↓
📅 Calendario inline → Seleziona data
    ↓
🕐 Selezione ora → Seleziona ora e minuti
    ↓
✅ Conferma → "Ora invia la foto"
    ↓
📸 Utente invia foto
    ↓
💾 Sistema salva post programmato nel database
```

### 2️⃣ Background Task Pubblica Automaticamente

```python
# In bot.py - parte automaticamente all'avvio
async def publish_scheduled_posts(bot: Bot):
    while True:
        await asyncio.sleep(60)  # Controlla ogni 60 secondi
        
        # Trova post scaduti
        due_posts = scheduler.get_due_posts()
        
        # Pubblica su Instagram
        for post in due_posts:
            await instagram.publish_photo(post.image_url, post.caption)
            scheduler.update_post_status(post.id, 'published')
```

## 💾 Schema Database

### Tabella: `user_sessions`
```sql
CREATE TABLE user_sessions (
    user_id INTEGER PRIMARY KEY,           -- ID utente Telegram
    scheduled_datetime TEXT,               -- DateTime completo programmato
    selected_date TEXT,                    -- Data selezionata
    selected_hour INTEGER,                 -- Ora selezionata
    selected_minute INTEGER,               -- Minuti selezionati
    last_updated TEXT,                     -- Ultimo aggiornamento
    extra_data TEXT                        -- Dati extra (JSON)
)
```

### Tabella: `scheduled_posts`
```sql
CREATE TABLE scheduled_posts (
    id TEXT PRIMARY KEY,                   -- ID univoco post
    user_id INTEGER NOT NULL,              -- ID utente Telegram
    image_url TEXT NOT NULL,               -- URL immagine su Steem
    caption TEXT,                          -- Caption post
    scheduled_time TEXT NOT NULL,          -- Quando pubblicare
    created_at TEXT NOT NULL,              -- Quando creato
    status TEXT DEFAULT 'scheduled',       -- Status: scheduled/published/failed/cancelled
    telegram_message_id INTEGER,           -- ID messaggio Telegram
    instagram_media_id TEXT,               -- ID media Instagram (dopo pubblicazione)
    error_message TEXT                     -- Messaggio errore (se failed)
)
```

## 🎯 Comandi Utente

### `/schedule` - Programma nuovo post
1. Mostra calendario interattivo
2. Utente seleziona data futura
3. Utente seleziona ora e minuti
4. Conferma e attende invio foto
5. Post viene programmato nel database

### `/scheduled` - Visualizza post programmati
```
📅 I tuoi post programmati:

⏰ 15/12/2025 14:30
   (in attesa di pubblicazione)

✅ 10/11/2025 10:00
   📸 Media ID: 123456789

❌ 05/11/2025 16:00
   ❌ Errore: Token scaduto
```

### Invia foto normale
- Se NON c'è sessione attiva → Pubblica immediatamente
- Se c'è sessione attiva → Programma per data/ora selezionate

## 🔧 API Database

### Sessioni Utente

```python
from services.database import db

# Salva sessione
db.save_user_session(
    user_id=123456,
    scheduled_datetime=datetime.now(),
    selected_hour=14
)

# Recupera sessione
session = db.get_user_session(123456)
# {'user_id': 123456, 'scheduled_datetime': ..., ...}

# Cancella sessione
db.clear_user_session(123456)
```

### Post Programmati

```python
from services.scheduler import scheduler

# Programma post
post_id = scheduler.schedule_post(
    user_id=123456,
    image_url="https://images.steem.blog/...",
    caption="My caption",
    scheduled_time=datetime(2025, 12, 15, 14, 30),
    telegram_message_id=789
)

# Recupera post utente
posts = scheduler.get_user_posts(123456)
posts = scheduler.get_user_posts(123456, status='scheduled')

# Recupera post scaduti (da pubblicare)
due_posts = scheduler.get_due_posts()

# Aggiorna status
scheduler.update_post_status(
    post_id,
    'published',
    instagram_media_id='IG123'
)

# Cancella post
scheduler.cancel_post(post_id, user_id=123456)
```

## ⚡️ Vantaggi del Nuovo Sistema

### ✅ Rispetto al Sistema Precedente (JSON)

| Aspetto | Prima (JSON) | Ora (SQLite) |
|---------|-------------|--------------|
| **Persistenza** | File JSON | Database relazionale |
| **Sessioni utente** | ❌ In messaggi Telegram | ✅ Tabella dedicata |
| **Query complesse** | ❌ Difficile | ✅ SQL nativo |
| **Concorrenza** | ⚠️ Race conditions | ✅ ACID transactions |
| **Performance** | ⚠️ Carica tutto in memoria | ✅ Query indicizzate |
| **Integrità dati** | ❌ Manuale | ✅ Foreign keys |
| **Pulizia automatica** | ❌ Manuale | ✅ Metodi dedicati |

### 🎯 Funzionalità Extra

```python
# Statistiche
stats = db.get_stats()
# {'active_sessions': 5, 'posts_scheduled': 10, 'posts_published': 50}

# Pulizia automatica
db.cleanup_old_sessions(days=7)    # Rimuove sessioni > 7 giorni
db.cleanup_old_posts(days=30)      # Rimuove post vecchi pubblicati/falliti
```

## 🧪 Test

```bash
# Test database
python services/database.py

# Test scheduler
python test_scheduling.py

# Test bot completo
python bot.py
```

## 🐛 Troubleshooting

### "Sessione scaduta"
- La sessione utente scade dopo aver programmato il post
- Se l'utente non invia la foto entro un tempo ragionevole, usare `/schedule` di nuovo

### Post non pubblicati
```python
# Controlla log
tail -f bot.log

# Verifica post scaduti
python -c "from services.scheduler import scheduler; posts = scheduler.get_due_posts(); print(posts)"
```

### Resetta database
```bash
# Backup
cp bot_data.db bot_data.db.backup

# Resetta
rm bot_data.db
python -c "from services.database import db; print('Database ricreato')"
```

## 📊 Monitoring

```python
from services.database import db

# Statistiche in tempo reale
stats = db.get_stats()
print(f"Sessioni attive: {stats['active_sessions']}")
print(f"Post programmati: {stats.get('posts_scheduled', 0)}")
print(f"Post pubblicati: {stats.get('posts_published', 0)}")
print(f"Post falliti: {stats.get('posts_failed', 0)}")
```

## 🚀 Produzione

### Raccomandazioni

1. **Backup regolare del database**
   ```bash
   cp bot_data.db backups/bot_data_$(date +%Y%m%d).db
   ```

2. **Pulizia periodica**
   ```python
   # Aggiungi in bot.py startup
   db.cleanup_old_sessions(days=7)
   db.cleanup_old_posts(days=30)
   ```

3. **Monitoring**
   - Controlla log per errori pubblicazione
   - Monitora dimensione database
   - Verifica post "stuck" in status scheduled

4. **Rate limiting Instagram**
   - Max ~200 post/ora
   - Non programmare troppi post ravvicinati
   - Il background task pubblica sequenzialmente

## ✅ Checklist Funzionalità

- ✅ Database SQLite con schema completo
- ✅ Sessioni utente persistenti
- ✅ Calendario interattivo
- ✅ Selezione ora/minuti
- ✅ Programmazione post futuri
- ✅ Background task pubblicazione automatica
- ✅ Comando /scheduled per visualizzare post
- ✅ Aggiornamento status post
- ✅ Gestione errori pubblicazione
- ✅ Pulizia automatica dati vecchi
- ✅ Statistiche database
- ✅ Test completi

## 🎉 Il Sistema Funziona!

Il bot è ora pronto per gestire post programmati in modo robusto e scalabile usando SQLite!

```bash
python bot.py
# 🚀 Bot avviato!
# Started scheduled posts publishing task
```
