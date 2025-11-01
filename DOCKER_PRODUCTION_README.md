# 🚀 Instagram Publisher Bot - Docker Production Setup

Questa guida spiega come deployare il bot Instagram Publisher in produzione usando Docker.

## 📋 Prerequisiti

- Docker e Docker Compose installati
- Token Telegram Bot
- Credenziali Steem
- Access Token Instagram
- (Opzionale) Credenziali Facebook App per refresh automatico token

## 🏗️ Build e Deploy

### 1. Configurazione Ambiente

```bash
# Copia il file di esempio ambiente
cp .env.docker .env

# Modifica .env con i tuoi valori reali
nano .env
```

### 2. Build dell'Immagine

```bash
# Build dell'immagine Docker
docker-compose build
```

### 3. Avvio del Bot

```bash
# Avvia il bot in background
docker-compose up -d

# Visualizza logs
docker-compose logs -f instagram-bot
```

### 4. Verifica Funzionamento

```bash
# Controlla stato container
docker-compose ps

# Verifica health check
docker-compose exec instagram-bot python -c "print('Bot attivo')"
```

## 📁 Struttura Volumi

Il container usa questi volumi per la persistenza:

- `./data/` - Database SQLite e dati persistenti
- `./temp/` - File temporanei durante l'elaborazione
- `./logs/` - File di log dell'applicazione

## 🔧 Comandi Utili

```bash
# Ferma il bot
docker-compose down

# Riavvia il bot
docker-compose restart

# Aggiorna il bot (dopo modifiche codice)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Visualizza logs in tempo reale
docker-compose logs -f

# Accedi al container
docker-compose exec instagram-bot bash

# Backup database
docker-compose exec instagram-bot cp /app/data/bot_data.db /app/data/bot_data_backup.db
```

## 🌐 Configurazione Webhook (Produzione)

Per usare il webhook mode in produzione:

1. Imposta `USE_WEBHOOK=true` nel `.env`
2. Configura `WEBHOOK_URL` con il tuo dominio pubblico
3. Assicurati che la porta 8080 sia esposta e raggiungibile
4. Il bot si registrerà automaticamente al webhook

## 🔒 Sicurezza

- **Non committare mai** il file `.env` su Git
- **Mantieni privato** `FACEBOOK_APP_SECRET`
- **Usa HTTPS** per i webhook in produzione
- **Backup regolare** del volume `./data/`

## 📊 Monitoraggio

Il container include health checks automatici. Puoi monitorare:

- Logs del container con `docker-compose logs`
- Stato del container con `docker-compose ps`
- Utilizzo risorse con `docker stats`

## 🆘 Troubleshooting

### Bot non si avvia
```bash
# Controlla logs per errori
docker-compose logs instagram-bot

# Verifica configurazione
docker-compose exec instagram-bot python -c "from config import config; print('Config OK')"
```

### Problemi database
```bash
# Verifica permessi volume
ls -la data/

# Ricrea database se corrotto
docker-compose exec instagram-bot rm /app/data/bot_data.db
```

### Problemi memoria/disco
```bash
# Pulisci Docker
docker system prune -a

# Verifica spazio disco
df -h
```

## 📝 Note Importanti

- Il bot usa SQLite come database, quindi è self-contained
- I file temporanei vengono automaticamente puliti
- Il container è configurato per riavviarsi automaticamente
- Usa health checks per verificare lo stato del servizio