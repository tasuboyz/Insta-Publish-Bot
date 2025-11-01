# Script PowerShell per avviare il bot
# Uso: .\start_bot.ps1

Write-Host "🤖 Instagram Publisher Bot - Avvio..." -ForegroundColor Cyan
Write-Host ""

# Verifica Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python non trovato! Installa Python 3.10+" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# Verifica .env
if (-not (Test-Path .env)) {
    Write-Host "⚠️  File .env non trovato!" -ForegroundColor Yellow
    Write-Host "   Copio .env.example in .env..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ""
    Write-Host "⚠️  IMPORTANTE: Configura .env prima di avviare il bot!" -ForegroundColor Yellow
    Write-Host "   Apri .env e compila:" -ForegroundColor Yellow
    Write-Host "   - TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    Write-Host "   - STEEM_USERNAME e STEEM_WIF" -ForegroundColor Yellow
    Write-Host "   - INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Premi INVIO per aprire .env con notepad..." -ForegroundColor Cyan
    Read-Host
    notepad .env
    Write-Host ""
    Write-Host "Dopo aver configurato .env, riesegui questo script." -ForegroundColor Cyan
    exit 0
}

# Verifica dipendenze
Write-Host "📦 Verifico dipendenze..." -ForegroundColor Cyan
try {
    python -c "import aiogram" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "aiogram non installato"
    }
    Write-Host "✅ Dipendenze OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Dipendenze mancanti, installo..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Errore installazione dipendenze" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🚀 Avvio bot..." -ForegroundColor Green
Write-Host "   (Premi Ctrl+C per terminare)" -ForegroundColor Gray
Write-Host ""

# Avvia bot
python bot.py
