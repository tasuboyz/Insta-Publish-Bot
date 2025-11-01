@echo off
REM Script di deploy per Instagram Publisher Bot (Windows)
REM Uso: deploy.bat [build|start|stop|restart|logs|cleanup]

setlocal enabledelayedexpansion

set "PROJECT_NAME=instagram-publisher-bot"
set "COMPOSE_FILE=docker-compose.yml"

REM Colori per output (limitati su Windows)
set "GREEN=[SUCCESS]"
set "YELLOW=[WARNING]"
set "RED=[ERROR]"
set "BLUE=[INFO]"

:log_info
echo %BLUE% %~1
goto :eof

:log_success
echo %GREEN% %~1
goto :eof

:log_warning
echo %YELLOW% %~1
goto :eof

:log_error
echo %RED% %~1
goto :eof

:check_env
if not exist ".env" (
    call :log_error "File .env non trovato!"
    call :log_info "Copia .env.docker in .env e configura le variabili"
    exit /b 1
)
goto :eof

:build
call :log_info "Building Docker image..."
docker-compose -f %COMPOSE_FILE% build --no-cache
if %errorlevel% equ 0 (
    call :log_success "Build completato"
) else (
    call :log_error "Errore durante il build"
    exit /b 1
)
goto :eof

:start
call :check_env
call :log_info "Avvio bot..."
docker-compose -f %COMPOSE_FILE% up -d
if %errorlevel% equ 0 (
    call :log_success "Bot avviato"
    call :log_info "Controlla logs con: deploy.bat logs"
) else (
    call :log_error "Errore avvio bot"
    exit /b 1
)
goto :eof

:stop
call :log_info "Fermo bot..."
docker-compose -f %COMPOSE_FILE% down
if %errorlevel% equ 0 (
    call :log_success "Bot fermato"
) else (
    call :log_error "Errore fermando bot"
    exit /b 1
)
goto :eof

:restart
call :stop
timeout /t 2 /nobreak > nul
call :start
goto :eof

:logs
call :log_info "Mostro logs (premi Ctrl+C per uscire)..."
docker-compose -f %COMPOSE_FILE% logs -f instagram-bot
goto :eof

:status
call :log_info "Stato container:"
docker-compose -f %COMPOSE_FILE% ps
goto :eof

:cleanup
call :log_warning "Pulisco container, immagini e volumi non utilizzati..."
docker-compose -f %COMPOSE_FILE% down -v
docker system prune -f
docker volume prune -f
call :log_success "Pulizia completata"
goto :eof

:backup
set "BACKUP_DIR=backups\%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "BACKUP_DIR=%BACKUP_DIR: =0%"

mkdir "%BACKUP_DIR%" 2>nul

call :log_info "Creo backup in %BACKUP_DIR%..."

REM Backup database
if exist "data" (
    xcopy "data" "%BACKUP_DIR%\data\" /E /I /H /Y >nul
    call :log_success "Database backup creato"
)

REM Backup configurazione
copy ".env" "%BACKUP_DIR%\.env.backup" >nul 2>&1
copy "docker-compose.yml" "%BACKUP_DIR%\" >nul 2>&1

call :log_success "Backup completato in %BACKUP_DIR%"
goto :eof

REM Main script logic
if "%1"=="build" goto build
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="cleanup" goto cleanup
if "%1"=="backup" goto backup

REM Help
echo Script di deploy per %PROJECT_NAME%
echo.
echo Uso: %0 [comando]
echo.
echo Comandi disponibili:
echo   build    - Build dell'immagine Docker
echo   start    - Avvia il bot
echo   stop     - Ferma il bot
echo   restart  - Riavvia il bot
echo   logs     - Mostra logs in tempo reale
echo   status   - Mostra stato container
echo   cleanup  - Pulisce container e volumi
echo   backup   - Crea backup dei dati
echo.
echo Esempi:
echo   %0 build ^& %0 start
echo   %0 logs
echo   %0 backup
goto :eof