"""
Script di avvio semplificato per il bot Instagram Publisher
Verifica configurazione e avvia il bot in modalità appropriata
"""
import sys
import os
from pathlib import Path

# Banner
BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   📸 Instagram Publisher Bot - Telegram                     ║
║                                                              ║
║   Bot automatico per pubblicare foto da Telegram            ║
║   su Instagram via Steem blockchain                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def check_python_version():
    """Verifica versione Python"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ richiesto!")
        print(f"   Versione attuale: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_env_file():
    """Verifica esistenza file .env"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  File .env non trovato!")
        print("   Creo .env da .env.example...")
        
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ File .env creato")
            print()
            print("⚠️  IMPORTANTE: Configura .env prima di continuare!")
            print("   Variabili richieste:")
            print("   - TELEGRAM_BOT_TOKEN")
            print("   - STEEM_USERNAME e STEEM_WIF")
            print("   - INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID")
            print()
            print(f"   Apri .env con: notepad {env_file}")
            
            # Chiedi se vuole aprire subito
            try:
                response = input("\n   Vuoi aprire .env ora? (s/n): ")
                if response.lower() in ['s', 'y', 'si', 'yes']:
                    os.system(f'notepad {env_file}')
                    print()
                    input("   Premi INVIO dopo aver configurato .env...")
            except KeyboardInterrupt:
                print("\n\n👋 Configurazione annullata")
                sys.exit(0)
        else:
            print("❌ .env.example non trovato!")
            sys.exit(1)
    else:
        print("✅ File .env trovato")


def check_dependencies():
    """Verifica dipendenze installate"""
    required = [
        ('aiogram', 'aiogram'),
        ('aiohttp', 'aiohttp'),
        ('beem', 'beem'),
        ('httpx', 'httpx'),
        ('PIL', 'Pillow'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing = []
    for module, package in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Dipendenze mancanti: {', '.join(missing)}")
        print("   Installo dipendenze...")
        print()
        
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Errore installazione dipendenze:")
            print(result.stderr)
            sys.exit(1)
        
        print("✅ Dipendenze installate")
    else:
        print("✅ Dipendenze OK")


def validate_config():
    """Valida configurazione"""
    try:
        from config import config
        
        errors = config.validate()
        if errors:
            print("⚠️  Errori configurazione:")
            for error in errors:
                print(f"   - {error}")
            print()
            print("   Correggi gli errori in .env e riprova")
            return False
        
        print("✅ Configurazione valida")
        
        # Mostra info modalità
        mode = "🌐 Webhook" if config.bot.use_webhook else "📡 Polling"
        print(f"   Modalità: {mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore caricamento configurazione: {e}")
        return False


def run_bot():
    """Avvia il bot"""
    try:
        print()
        print("=" * 62)
        print("🚀 Avvio bot...")
        print("   (Premi Ctrl+C per terminare)")
        print("=" * 62)
        print()
        
        # Importa e avvia bot
        from bot import main
        main()
        
    except KeyboardInterrupt:
        print("\n\n👋 Bot terminato dall'utente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point principale"""
    print(BANNER)
    print("🔍 Verifico ambiente di esecuzione...\n")
    
    # 1. Verifica Python
    check_python_version()
    
    # 2. Verifica .env
    check_env_file()
    
    # 3. Verifica dipendenze
    check_dependencies()
    
    print()
    print("🔧 Validazione configurazione...\n")
    
    # 4. Valida configurazione
    if not validate_config():
        sys.exit(1)
    
    # 5. Avvia bot
    run_bot()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Errore fatale: {e}")
        sys.exit(1)
