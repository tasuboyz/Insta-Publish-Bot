"""
Instagram Publisher - Gestisce la pubblicazione di contenuti su Instagram
tramite Facebook Graph API (Instagram Business Account)

Requisiti:
- Facebook App con permessi: instagram_basic, instagram_content_publish
- Instagram Business Account collegato a Facebook Page
- Access Token con i permessi necessari

Workflow Instagram:
1. Crea container con POST /{ig-user-id}/media
2. Pubblica container con POST /{ig-user-id}/media_publish
"""

import os
import time
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InstagramPublisher:
    """Gestisce la pubblicazione su Instagram tramite Facebook Graph API"""
    
    def __init__(self, access_token: str = None, instagram_account_id: str = None):
        """
        Inizializza Instagram Publisher
        
        Args:
            access_token: Facebook/Instagram access token
            instagram_account_id: Instagram Business Account ID (formato: 17841465903297752)
        """
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = instagram_account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.graph_api_version = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v23.0")
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"
        
        if not self.access_token:
            raise ValueError("Instagram access_token non configurato")
        if not self.instagram_account_id:
            raise ValueError("Instagram account_id non configurato")
    
    def create_media_container(self, image_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Crea un container media su Instagram (step 1)
        
        Args:
            image_url: URL pubblico dell'immagine (deve essere accessibile da Facebook)
            caption: Didascalia del post (max 2200 caratteri)
            
        Returns:
            dict: {'id': 'container_id', 'status_code': 'IN_PROGRESS'}
        """
        try:
            endpoint = f"{self.base_url}/{self.instagram_account_id}/media"
            
            params = {
                "image_url": image_url,
                "access_token": self.access_token
            }
            
            if caption:
                params["caption"] = caption[:2200]  # Instagram limit
            
            logger.info(f"📸 Creazione container Instagram per: {image_url}")
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Container creato: {result.get('id')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore creazione container: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Risposta API: {e.response.text}")
            raise Exception(f"Impossibile creare container Instagram: {e}")
    
    def publish_media(self, creation_id: str) -> Dict[str, Any]:
        """
        Pubblica il container media su Instagram (step 2)
        
        Args:
            creation_id: ID del container creato in step 1
            
        Returns:
            dict: {'id': 'media_id'}
        """
        try:
            endpoint = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            
            params = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            
            logger.info(f"📤 Pubblicazione container: {creation_id}")
            
            response = requests.post(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            media_id = result.get('id')
            
            logger.info(f"✅ Post pubblicato! Media ID: {media_id}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore pubblicazione: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Risposta API: {e.response.text}")
            raise Exception(f"Impossibile pubblicare su Instagram: {e}")
    
    def publish_photo(self, image_url: str, caption: str = "", wait_for_ready: bool = True) -> Dict[str, Any]:
        """
        Pubblica una foto su Instagram (workflow completo)
        
        Args:
            image_url: URL pubblico dell'immagine
            caption: Didascalia del post
            wait_for_ready: Se True, attende che il container sia pronto prima di pubblicare
            
        Returns:
            dict: Informazioni complete sulla pubblicazione
        """
        try:
            # Step 1: Crea container
            container = self.create_media_container(image_url, caption)
            creation_id = container.get('id')
            
            if not creation_id:
                raise Exception("Container ID non ottenuto dalla risposta API")
            
            # Step 2: Attendi che il container sia pronto (opzionale)
            if wait_for_ready:
                logger.info("⏳ Attesa elaborazione container...")
                time.sleep(5)  # Instagram necessita qualche secondo per processare
            
            # Step 3: Pubblica
            media = self.publish_media(creation_id)
            
            return {
                "success": True,
                "container_id": creation_id,
                "media_id": media.get('id'),
                "image_url": image_url,
                "caption": caption,
                "published_at": datetime.now().isoformat(),
                "instagram_url": f"https://www.instagram.com/p/{self._get_media_code(media.get('id'))}" if media.get('id') else None
            }
            
        except Exception as e:
            logger.error(f"❌ Errore pubblicazione Instagram completa: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_url": image_url
            }
    
    def _get_media_code(self, media_id: str) -> Optional[str]:
        """
        Ottiene il codice media per costruire URL Instagram
        (opzionale - richiede chiamata API aggiuntiva)
        """
        try:
            endpoint = f"{self.base_url}/{media_id}"
            params = {
                "fields": "shortcode",
                "access_token": self.access_token
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json().get('shortcode')
            
        except Exception as e:
            logger.warning(f"Impossibile ottenere shortcode: {e}")
            return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sull'account Instagram configurato
        
        Returns:
            dict: Info account (username, profile_picture_url, followers_count, etc.)
        """
        try:
            endpoint = f"{self.base_url}/{self.instagram_account_id}"
            params = {
                "fields": "username,name,profile_picture_url,followers_count,follows_count,media_count",
                "access_token": self.access_token
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Errore recupero info account: {e}")
            raise


# Esempio di utilizzo
if __name__ == "__main__":
    # Test del modulo (richiede configurazione .env)
    logging.basicConfig(level=logging.INFO)
    
    try:
        publisher = InstagramPublisher()
        
        # Info account
        info = publisher.get_account_info()
        print(f"📱 Account: @{info.get('username')}")
        print(f"👥 Followers: {info.get('followers_count')}")
        
        # Test pubblicazione (commenta per evitare post reali)
        # result = publisher.publish_photo(
        #     image_url="https://example.com/image.jpg",
        #     caption="Test post da API Python"
        # )
        # print(f"Risultato: {result}")
        
    except Exception as e:
        print(f"Errore: {e}")
