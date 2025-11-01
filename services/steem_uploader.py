"""
Servizio asincrono per upload immagini su Steem blockchain
"""
import asyncio
from typing import Optional
from beem import Steem
from beem.imageuploader import ImageUploader
import logging
import requests
import time

logger = logging.getLogger(__name__)


class SteemNodeTester:
    """Classe per testare e trovare il nodo Steem più veloce"""

    def __init__(self):
        self.fastest_node = None
        self.blacklist = set()

    def get_steem_servers(self) -> Optional[list[str]]:
        """Ottiene lista nodi Steem disponibili"""
        url = "https://steem.senior.workers.dev/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                steem_servers = data.get('__steem_servers__', [])
                logger.info(f"Trovati {len(steem_servers)} nodi Steem disponibili")
                return steem_servers
            else:
                logger.warning(f"Errore richiesta server: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Errore connessione server lista nodi: {e}")
            return None

    def test_node(self, node: str) -> float:
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

            response_time = end_time - start_time
            logger.debug(f"Nodo {node}: {response_time:.3f}s")
            return response_time

        except Exception as e:
            logger.debug(f"Errore test nodo {node}: {e}")
            self.blacklist.add(node)
            return float('inf')

    def find_fastest_node(self, fallback_nodes: list[str] = None) -> Optional[str]:
        """Trova il nodo più veloce disponibile"""
        nodes = self.get_steem_servers()
        
        # Se non riusciamo a ottenere la lista dinamica, usa i nodi di fallback
        if not nodes:
            logger.info("Uso nodi di fallback")
            nodes = fallback_nodes or ['https://api.steemit.com', 'https://api.steemdb.com']

        fastest_time = float('inf')
        fastest_node = None

        logger.info("Ricerca del nodo più veloce...")
        for node in nodes[:10]:  # Testa solo i primi 10 per velocità
            response_time = self.test_node(node)
            if response_time < fastest_time:
                fastest_time = response_time
                fastest_node = node

        if fastest_node:
            logger.info(f"✅ Nodo più veloce: {fastest_node} ({fastest_time:.3f}s)")
            self.fastest_node = fastest_node
        else:
            logger.warning("⚠️ Nessun nodo disponibile trovato")

        return fastest_node


class SteemUploader:
    """Upload immagini su Steem blockchain (async wrapper)"""

    def __init__(self, username: str, wif: str, nodes: list[str], auto_find_fastest: bool = True):
        """
        Inizializza uploader

        Args:
            username: Username Steem
            wif: Chiave privata posting (WIF format)
            nodes: Lista di nodi RPC (usati come fallback)
            auto_find_fastest: Se True, cerca automaticamente il nodo più veloce
        """
        self.username = username
        self.wif = wif
        self.fallback_nodes = nodes
        self.auto_find_fastest = auto_find_fastest
        self.active_nodes = nodes.copy()
        self.node_tester = SteemNodeTester()
        
        # Se abilitato, trova il nodo più veloce all'inizializzazione
        if auto_find_fastest:
            self._update_fastest_node()

    def _update_fastest_node(self):
        """Aggiorna al nodo più veloce disponibile"""
        try:
            fastest = self.node_tester.find_fastest_node(self.fallback_nodes)
            if fastest:
                # Metti il nodo più veloce in testa alla lista
                self.active_nodes = [fastest] + [n for n in self.fallback_nodes if n != fastest]
                logger.info(f"Nodi attivi ordinati: {self.active_nodes[:3]}...")
            else:
                logger.warning("Uso nodi di fallback senza ordinamento")
                self.active_nodes = self.fallback_nodes
        except Exception as e:
            logger.warning(f"Errore ricerca nodo veloce: {e}, uso fallback")
            self.active_nodes = self.fallback_nodes

    async def update_fastest_node_async(self):
        """Versione asincrona di update_fastest_node"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._update_fastest_node)

    async def upload_image(self, file_path: str) -> Optional[str]:
        """
        Upload immagine su blockchain (async)

        Args:
            file_path: Percorso file immagine

        Returns:
            URL immagine su images.steem.blog o None se errore
        """
        try:
            # beem è sincrono, quindi eseguiamo in thread pool
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                self._upload_sync,
                file_path
            )
            return url
        except Exception as e:
            logger.error(f"Errore upload Steem: {e}")
            return None

    def _upload_sync(self, file_path: str) -> str:
        """Upload sincrono (eseguito in thread pool)"""
        logger.info(f"📤 Upload immagine: {file_path}")
        logger.info(f"👤 Username: {self.username}")
        logger.info(f"🌐 Nodi: {self.active_nodes[:2]}")
        
        # Inizializza connessione Steem
        steem = Steem(
            node=self.active_nodes,
            keys=[self.wif]
        )

        # Upload immagine
        uploader = ImageUploader(blockchain_instance=steem)
        result = uploader.upload(
            file_path,
            self.username
        )

        logger.info("✅ Immagine caricata con successo!")
        logger.info(f"🔗 URL: {result['url']}")
        
        # Restituisci URL
        return result['url']

    async def test_connection(self) -> bool:
        """Test connessione ai nodi"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._test_connection_sync
            )
            return True
        except Exception as e:
            logger.error(f"Test connessione fallito: {e}")
            return False

    def _test_connection_sync(self):
        """Test connessione sincrono"""
        steem = Steem(node=self.active_nodes)
        # Prova a ottenere info blockchain
        version = steem.get_blockchain_version()
        logger.info(f"Blockchain version: {version}")


if __name__ == "__main__":
    # Test
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        print("🧪 Test SteemUploader con ricerca nodo automatica\n")
        
        uploader = SteemUploader(
            username=os.getenv('STEEM_USERNAME', ''),
            wif=os.getenv('STEEM_WIF', ''),
            nodes=['https://api.steemit.com', 'https://api.steemdb.com', 'https://steemd.minnowsupportproject.org'],
            auto_find_fastest=True
        )
        
        print(f"\n📋 Nodi configurati: {uploader.active_nodes[:3]}")
        
        # Test connessione
        print("\n🔍 Test connessione...")
        ok = await uploader.test_connection()
        print(f"Connessione: {'✅ OK' if ok else '❌ ERRORE'}")
        
        # Test ricerca nodo dinamica
        print("\n🔄 Aggiornamento nodo più veloce...")
        await uploader.update_fastest_node_async()
        print(f"Nodi dopo aggiornamento: {uploader.active_nodes[:3]}")
    
    asyncio.run(test())
