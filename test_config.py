"""
Script di test rapido per verificare la configurazione
"""
import asyncio
import sys
from config import config
from services.steem_uploader import SteemUploader
from services.instagram_publisher_async import InstagramPublisher


async def test_configuration():
    """Test configurazione e connessioni"""
    print("🧪 Test Configurazione Bot\n")
    print("=" * 50)
    
    # 1. Valida configurazione
    print("\n1️⃣ Validazione configurazione...")
    errors = config.validate()
    if errors:
        print("❌ Errori trovati:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ Configurazione valida")
    
    # 2. Test Steem
    print("\n2️⃣ Test connessione Steem...")
    try:
        steem = SteemUploader(
            username=config.steem.username,
            wif=config.steem.wif,
            nodes=config.steem.nodes,
            auto_find_fastest=config.steem.auto_find_fastest
        )
        steem_ok = await steem.test_connection()
        if steem_ok:
            print(f"✅ Connesso a Steem")
            print(f"   Username: {config.steem.username}")
            print(f"   Nodi attivi: {', '.join(steem.active_nodes[:2])}...")
            print(f"   Auto-find: {'✅ Abilitato' if config.steem.auto_find_fastest else '❌ Disabilitato'}")
        else:
            print("❌ Errore connessione Steem")
            return False
    except Exception as e:
        print(f"❌ Errore Steem: {e}")
        return False
    
    # 3. Test Instagram
    print("\n3️⃣ Test connessione Instagram...")
    try:
        instagram = InstagramPublisher(
            access_token=config.instagram.access_token,
            account_id=config.instagram.account_id
        )
        ig_info = await instagram.get_account_info()
        if ig_info:
            print(f"✅ Connesso a Instagram")
            print(f"   Account: @{ig_info.get('username')}")
            print(f"   Followers: {ig_info.get('followers_count', 0):,}")
            print(f"   Posts: {ig_info.get('media_count', 0)}")
        else:
            print("❌ Errore connessione Instagram")
            return False
    except Exception as e:
        print(f"❌ Errore Instagram: {e}")
        return False
    
    # 4. Verifica modalità bot
    print("\n4️⃣ Configurazione bot...")
    mode = "Webhook" if config.bot.use_webhook else "Polling"
    print(f"✅ Modalità: {mode}")
    if config.bot.use_webhook:
        print(f"   URL: {config.bot.webhook_url}{config.bot.webhook_path}")
        print(f"   Host: {config.bot.web_app_host}:{config.bot.web_app_port}")
    
    print("\n" + "=" * 50)
    print("✅ Tutti i test passati! Bot pronto per l'avvio.")
    print("\nAvvia il bot con: python bot.py")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_configuration())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrotto")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        sys.exit(1)
