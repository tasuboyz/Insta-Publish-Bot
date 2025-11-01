"""
Test rapido per verificare che il modulo semplificato funzioni
Esegui dopo aver installato le dipendenze: pip install -r requirements.txt
"""

try:
    from utils.steem_request import Blockchain, SteemNodeTester
    print("✅ Import classi riuscito!")

    # Test inizializzazione
    blockchain = Blockchain()
    print("✅ Blockchain inizializzata!")

    tester = SteemNodeTester()
    print("✅ SteemNodeTester inizializzato!")

    # Test metodi disponibili
    methods = [method for method in dir(blockchain) if not method.startswith('_')]
    print(f"📋 Metodi Blockchain disponibili: {methods}")

    print("\n🎉 Modulo semplificato funzionante!")
    print("💡 Ora puoi installare beem e testare l'upload:")
    print("   pip install beem")
    print("   python main.py")

except ImportError as e:
    print(f"❌ Errore import: {e}")
except Exception as e:
    print(f"❌ Errore: {e}")