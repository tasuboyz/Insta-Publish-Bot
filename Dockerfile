# Dockerfile per Instagram Publisher Bot - Produzione
FROM python:3.11-slim

# Imposta working directory
WORKDIR /app

# Installa dipendenze di sistema necessarie
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY . .

# Crea directory per dati persistenti e temporanei
RUN mkdir -p /app/data /app/temp /app/logs

# Imposta variabili d'ambiente di default
ENV PYTHONPATH=/app
ENV TEMP_DIR=/app/temp
ENV DATABASE_PATH=/app/data/bot_data.db

# Crea utente non-root per sicurezza
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Comando di avvio
CMD ["python", "run.py"]