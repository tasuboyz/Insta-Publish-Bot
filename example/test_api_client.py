"""
Client di esempio per testare l'API di upload immagini
Questo script mostra come utilizzare l'API per caricare immagini
"""

import os
import requests
from pathlib import Path

class SteemImageUploadClient:
    """Client per interagire con l'API di upload immagini"""
    
    def __init__(self, api_url="http://127.0.0.1:5000"):
        """
        Inizializza il client
        
        Args:
            api_url: URL base dell'API
        """
        self.api_url = api_url.rstrip('/')
    
    def get_api_info(self):
        """Ottiene informazioni sull'API"""
        try:
            response = requests.get(f"{self.api_url}/")
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Errore di connessione: {e}"}
    
    def check_health(self):
        """Verifica lo stato dell'API"""
        try:
            response = requests.get(f"{self.api_url}/health")
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Errore di connessione: {e}"}
    
    def upload_single_image(self, file_path):
        """
        Carica una singola immagine
        
        Args:
            file_path: Percorso del file da caricare
            
        Returns:
            dict: Risposta dell'API
        """
        if not os.path.exists(file_path):
            return {"error": f"File non trovato: {file_path}"}
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(f"{self.api_url}/upload", files=files)
                return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Errore di connessione: {e}"}
        except Exception as e:
            return {"error": f"Errore: {e}"}
    
    def upload_multiple_images(self, file_paths):
        """
        Carica multiple immagini
        
        Args:
            file_paths: Lista di percorsi dei file da caricare
            
        Returns:
            dict: Risposta dell'API
        """
        # Verifica che tutti i file esistano
        existing_files = []
        missing_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        if missing_files:
            return {
                "error": f"File non trovati: {missing_files}",
                "existing_files": existing_files
            }
        
        try:
            files = []
            file_objects = []
            
            # Apre tutti i file
            for file_path in existing_files:
                f = open(file_path, 'rb')
                file_objects.append(f)
                files.append(('files', (os.path.basename(file_path), f)))
            
            try:
                response = requests.post(f"{self.api_url}/upload-multiple", files=files)
                return response.json()
            finally:
                # Chiude tutti i file
                for f in file_objects:
                    f.close()
                    
        except requests.exceptions.RequestException as e:
            return {"error": f"Errore di connessione: {e}"}
        except Exception as e:
            return {"error": f"Errore: {e}"}

def print_response(response, title="Risposta"):
    """Stampa una risposta in formato leggibile"""
    print(f"\n📋 {title}")
    print("-" * 50)
    
    if "error" in response:
        print(f"❌ Errore: {response['error']}")
        return
    
    if "success" in response:
        if response["success"]:
            print("✅ Successo!")
        else:
            print("❌ Fallimento")
    
    # Stampa le informazioni principali
    if "message" in response:
        print(f"💬 {response['message']}")
    
    if "data" in response:
        data = response["data"]
        
        # Upload singolo
        if "url" in data:
            print(f"🔗 URL: {data['url']}")
            print(f"📄 File: {data.get('filename', 'N/A')}")
            print(f"👤 Caricato da: {data.get('uploaded_by', 'N/A')}")
        
        # Upload multipli
        elif "successful_uploads" in data and "failed_uploads" in data:
            print(f"📊 Statistiche:")
            print(f"   ✅ Successi: {data.get('successful_count', 0)}")
            print(f"   ❌ Fallimenti: {data.get('failed_count', 0)}")
            print(f"   📁 Totale: {data.get('total_files', 0)}")
            
            if data.get("successful_uploads"):
                print(f"\n🎉 Upload riusciti:")
                for upload in data["successful_uploads"]:
                    print(f"   📄 {upload['filename']}")
                    print(f"   🔗 {upload['url']}")
            
            if data.get("failed_uploads"):
                print(f"\n💥 Upload falliti:")
                for upload in data["failed_uploads"]:
                    print(f"   📄 {upload['filename']}: {upload['error']}")
    
    # Stampa info API
    elif "status" in response:
        print(f"🟢 Stato: {response['status']}")
        if "username" in response:
            print(f"👤 Username: {response['username']}")
        if "supported_formats" in response:
            print(f"🖼️  Formati supportati: {', '.join(response['supported_formats'])}")
        if "max_file_size_mb" in response:
            print(f"📏 Dimensione max: {response['max_file_size_mb']}MB")

def main():
    """Funzione principale di esempio"""
    print("🎯 Client di test per Steem Image Upload API")
    print("=" * 60)
    
    # Inizializza il client
    client = SteemImageUploadClient()
    
    # 1. Controlla le informazioni dell'API
    print("\n🔍 1. Controllo informazioni API...")
    api_info = client.get_api_info()
    print_response(api_info, "Informazioni API")
    
    # 2. Controlla lo stato dell'API
    print("\n🏥 2. Controllo stato API...")
    health = client.check_health()
    print_response(health, "Stato API")
    
    # Se l'API non è healthy, ferma qui
    if health.get("status") != "healthy":
        print("\n⚠️  L'API non è in stato healthy. Controlla la configurazione.")
        return
    
    # 3. Test upload singola immagine
    print("\n📤 3. Test upload singola immagine...")
    
    # Cerca file di esempio nella directory
    sample_files = []
    for ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        pattern = f"*.{ext}"
        files = list(Path('.').glob(pattern))
        sample_files.extend(files)
    
    if sample_files:
        test_file = str(sample_files[0])
        print(f"📁 Usando file di esempio: {test_file}")
        
        result = client.upload_single_image(test_file)
        print_response(result, "Upload singola immagine")
    else:
        print("⚠️  Nessun file immagine trovato nella directory corrente")
        print("💡 Aggiungi un'immagine (.jpg, .png, .gif, ecc.) per testare l'upload")
    
    # 4. Test upload multiple immagini
    if len(sample_files) > 1:
        print("\n📤📤 4. Test upload multiple immagini...")
        
        # Prende i primi 3 file per il test
        test_files = [str(f) for f in sample_files[:3]]
        print(f"📁 Usando file: {', '.join([Path(f).name for f in test_files])}")
        
        result = client.upload_multiple_images(test_files)
        print_response(result, "Upload multiple immagini")
    else:
        print("\n📤📤 4. Skip test upload multiple immagini (servono almeno 2 file)")
    
    print("\n🎊 Test completato!")
    print("💡 Suggerimenti:")
    print("   - Assicurati che il server API sia in esecuzione")
    print("   - Controlla la configurazione nel file .env")
    print("   - Verifica che ci siano file immagine nella directory per i test")

if __name__ == "__main__":
    main()