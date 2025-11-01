"""
Esempio semplice per caricare immagini su Steem
Utilizza la funzione steem_upload_image esistente
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(__file__))

# Importa la classe Blockchain
from command.basic.steem_request import Blockchain

# Carica le variabili d'ambiente
load_dotenv()

class SteemImageUploader:
    """Classe per gestire l'upload di immagini su Steem"""
    
    def __init__(self, username=None, wif=None):
        """
        Inizializza l'uploader
        
        Args:
            username: Username Steem (se None, usa la variabile d'ambiente)
            wif: Private posting key (se None, usa la variabile d'ambiente)
        """
        self.blockchain = Blockchain()
        self.username = username or os.getenv("STEEM_USERNAME")
        self.wif = wif or os.getenv("STEEM_WIF")
        
        if not self.username or not self.wif:
            raise ValueError("Username e WIF devono essere forniti o configurati nel file .env")
    
    def upload_image(self, file_path):
        """
        Carica un'immagine su Steem
        
        Args:
            file_path: Percorso del file da caricare
            
        Returns:
            dict: Risultato dell'upload con URL dell'immagine
        """
        # Verifica che il file esista
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File non trovato: {file_path}")
        
        # Verifica che sia un'immagine
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension not in valid_extensions:
            raise ValueError(f"Formato file non supportato: {file_extension}. Formati supportati: {valid_extensions}")
        
        print(f"📤 Caricamento immagine: {file_path}")
        print(f"👤 Username: {self.username}")
        
        try:
            # Usa la funzione esistente per caricare l'immagine
            result = self.blockchain.steem_upload_image(file_path, self.username, self.wif)
            
            print("✅ Immagine caricata con successo!")
            print(f"🔗 Risultato: {result}")
            
            return {
                "success": True,
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "result": result,
                "username": self.username
            }
            
        except Exception as e:
            print(f"❌ Errore durante l'upload: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "error": str(e),
                "username": self.username
            }
    
    def upload_multiple_images(self, file_paths):
        """
        Carica multiple immagini
        
        Args:
            file_paths: Lista di percorsi dei file da caricare
            
        Returns:
            list: Lista dei risultati per ogni file
        """
        results = []
        
        for file_path in file_paths:
            print(f"\n--- Upload {len(results) + 1}/{len(file_paths)} ---")
            result = self.upload_image(file_path)
            results.append(result)
        
        # Statistiche finali
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        print(f"\n📊 Risultati finali:")
        print(f"✅ Successi: {successful}")
        print(f"❌ Fallimenti: {failed}")
        print(f"📁 Totale: {len(results)}")
        
        return results


def main():
    """Funzione principale di esempio"""
    
    print("🎯 Steem Image Uploader - Esempio di utilizzo")
    print("=" * 50)
    
    try:
        # Inizializza l'uploader
        uploader = SteemImageUploader()
        
        # Esempio 1: Upload singola immagine
        print("\n🖼️  ESEMPIO 1: Upload singola immagine")
        
        # Percorso di esempio (modifica questo con il tuo file)
        image_path = "esempio.jpg"  # Cambia questo percorso
        
        if os.path.exists(image_path):
            result = uploader.upload_image(image_path)
            
            if result["success"]:
                print(f"🎉 Upload completato!")
                print(f"📄 File: {result['filename']}")
                print(f"🔗 URL: {result['result']}")
            else:
                print(f"💥 Upload fallito: {result['error']}")
        else:
            print(f"⚠️  File di esempio non trovato: {image_path}")
            print("💡 Modifica il percorso 'image_path' nel codice con un'immagine esistente")
        
        # Esempio 2: Upload multiple immagini
        print("\n🖼️  ESEMPIO 2: Upload multiple immagini")
        
        # Lista di percorsi di esempio (modifica questi con i tuoi file)
        image_paths = [
            "immagine1.jpg",
            "immagine2.png",
            "immagine3.gif"
        ]
        
        # Filtra solo i file esistenti
        existing_files = [path for path in image_paths if os.path.exists(path)]
        
        if existing_files:
            results = uploader.upload_multiple_images(existing_files)
            
            print("\n📝 Riepilogo dettagliato:")
            for i, result in enumerate(results, 1):
                status = "✅" if result["success"] else "❌"
                print(f"{i}. {status} {result['filename']}")
                if result["success"]:
                    print(f"   🔗 URL: {result['result']}")
                else:
                    print(f"   💥 Errore: {result['error']}")
        else:
            print("⚠️  Nessun file di esempio trovato")
            print("💡 Aggiungi alcuni file immagine alla directory del progetto")
    
    except ValueError as e:
        print(f"⚙️  Errore di configurazione: {e}")
        print("💡 Assicurati di aver configurato STEEM_USERNAME e STEEM_WIF nel file .env")
    except Exception as e:
        print(f"💥 Errore: {e}")


if __name__ == "__main__":
    main()