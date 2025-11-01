"""
Modulo semplificato per upload immagini su Steem/Hive blockchain
Contiene solo le funzionalità necessarie per l'API di upload immagini
"""

from beem import Steem
from beem.imageuploader import ImageUploader
import requests
import time


class SteemNodeTester:
    """Classe per testare e trovare il nodo Steem più veloce"""

    def __init__(self, mode='irreversible'):
        self.mode = mode
        self.fastest_node = None
        self.blacklist = set()

    def get_steem_servers(self):
        """Ottiene lista nodi Steem disponibili"""
        url = "https://steem.senior.workers.dev/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                steem_servers = data.get('__steem_servers__', [])
                return steem_servers
            else:
                print(f"Errore richiesta server: {response.status_code}")
                return None
        except Exception as e:
            print(f"Errore connessione server: {e}")
            return None

    def test_node(self, node):
        """Testa velocità di un singolo nodo"""
        if node in self.blacklist:
            return float('inf')

        try:
            # Test connessione HTTP
            response = requests.get(node, timeout=5)
            if response.status_code != 200:
                raise Exception(f"Nodo {node} status {response.status_code}")

            # Test connessione blockchain
            steem = Steem(node=node)
            start_time = time.time()
            steem.get_config()
            end_time = time.time()

            return end_time - start_time

        except Exception as e:
            print(f"Errore test nodo {node}: {e}")
            self.blacklist.add(node)
            return float('inf')

    def find_fastest_node(self):
        """Trova il nodo più veloce disponibile"""
        nodes = self.get_steem_servers()
        if not nodes:
            return None

        fastest_time = float('inf')
        fastest_node = None

        for node in nodes:
            response_time = self.test_node(node)
            if response_time < fastest_time:
                fastest_time = response_time
                fastest_node = node

        self.fastest_node = fastest_node
        return fastest_node


class Blockchain:
    """Classe semplificata per operazioni blockchain necessarie all'upload immagini"""

    def __init__(self, mode='irreversible'):
        self.mode = mode
        self.tester = SteemNodeTester()
        self.steem_node = None

    def update_node(self):
        """Aggiorna al nodo più veloce disponibile"""
        new_node = self.tester.find_fastest_node()
        if new_node:
            self.steem_node = new_node
            print(f"✅ Nodo aggiornato: {self.steem_node}")
        else:
            print("⚠️ Impossibile trovare nodi disponibili")
            # Fallback a un nodo conosciuto
            self.steem_node = "https://api.steemit.com"

    def steem_upload_image(self, file_path, username, wif):
        """
        Carica un'immagine su Steem blockchain

        Args:
            file_path: Percorso del file da caricare
            username: Username Steem
            wif: Chiave privata posting

        Returns:
            URL dell'immagine caricata
        """
        # Assicurati di avere un nodo valido
        if not self.steem_node:
            self.update_node()

        try:
            print(f"📤 Upload immagine: {file_path}")
            print(f"👤 Username: {username}")
            print(f"🌐 Nodo: {self.steem_node}")

            # Inizializza connessione Steem
            stm = Steem(keys=[wif], node=self.steem_node, rpcuser=username)

            # Carica immagine
            uploader = ImageUploader(blockchain_instance=stm)
            result = uploader.upload(file_path, username)

            print("✅ Immagine caricata con successo!")
            print(f"🔗 Risultato: {result}")

            return result

        except Exception as e:
            print(f"❌ Errore upload: {e}")
            raise Exception(f"Upload fallito: {e}")