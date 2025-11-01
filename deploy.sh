#!/bin/bash

# Script di deploy per Instagram Publisher Bot
# Uso: ./deploy.sh [build|start|stop|restart|logs|cleanup]

set -e

PROJECT_NAME="instagram-publisher-bot"
COMPOSE_FILE="docker-compose.yml"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_env() {
    if [ ! -f ".env" ]; then
        log_error "File .env non trovato!"
        log_info "Copia .env.docker in .env e configura le variabili"
        exit 1
    fi
}

build() {
    log_info "Building Docker image..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    log_success "Build completato"
}

start() {
    check_env
    log_info "Avvio bot..."
    docker-compose -f $COMPOSE_FILE up -d
    log_success "Bot avviato"
    log_info "Controlla logs con: ./deploy.sh logs"
}

stop() {
    log_info "Fermo bot..."
    docker-compose -f $COMPOSE_FILE down
    log_success "Bot fermato"
}

restart() {
    stop
    sleep 2
    start
}

logs() {
    log_info "Mostro logs (premi Ctrl+C per uscire)..."
    docker-compose -f $COMPOSE_FILE logs -f instagram-bot
}

status() {
    log_info "Stato container:"
    docker-compose -f $COMPOSE_FILE ps
}

cleanup() {
    log_warning "Pulisco container, immagini e volumi non utilizzati..."
    docker-compose -f $COMPOSE_FILE down -v
    docker system prune -f
    docker volume prune -f
    log_success "Pulizia completata"
}

backup() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    log_info "Creo backup in $BACKUP_DIR..."

    # Backup database
    if [ -d "data" ]; then
        cp -r data "$BACKUP_DIR/"
        log_success "Database backup creato"
    fi

    # Backup configurazione (senza secrets)
    cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || true
    cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true

    log_success "Backup completato in $BACKUP_DIR"
}

case "${1:-help}" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    backup)
        backup
        ;;
    *)
        echo "Script di deploy per $PROJECT_NAME"
        echo ""
        echo "Uso: $0 [comando]"
        echo ""
        echo "Comandi disponibili:"
        echo "  build    - Build dell'immagine Docker"
        echo "  start    - Avvia il bot"
        echo "  stop     - Ferma il bot"
        echo "  restart  - Riavvia il bot"
        echo "  logs     - Mostra logs in tempo reale"
        echo "  status   - Mostra stato container"
        echo "  cleanup  - Pulisce container e volumi"
        echo "  backup   - Crea backup dei dati"
        echo ""
        echo "Esempi:"
        echo "  $0 build && $0 start"
        echo "  $0 logs"
        echo "  $0 backup"
        ;;
esac