"""
Servizio asincrono per pubblicazione su Instagram
"""
import asyncio
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class InstagramPublisher:
    """Pubblicazione foto su Instagram (async)"""
    
    def __init__(self, access_token: str, account_id: str, api_version: str = "v23.0"):
        """
        Inizializza publisher
        
        Args:
            access_token: Facebook/Instagram access token
            account_id: Instagram Business Account ID
            api_version: Versione Graph API
        """
        self.access_token = access_token
        self.account_id = account_id
        self.base_url = f"https://graph.facebook.com/{api_version}"
    
    async def create_container(self, image_url: str, caption: str = "") -> Optional[str]:
        """
        Crea container Instagram (Step 1)
        
        Args:
            image_url: URL pubblico immagine
            caption: Didascalia post
        
        Returns:
            Container ID o None se errore
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.account_id}/media",
                    data={
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": self.access_token
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                container_id = data.get('id')
                logger.info(f"Container creato: {container_id}")
                return container_id
                
        except Exception as e:
            logger.error(f"Errore creazione container: {e}")
            return None
    
    async def publish_container(self, container_id: str) -> Optional[str]:
        """
        Pubblica container su Instagram (Step 2)
        
        Args:
            container_id: ID container da pubblicare
        
        Returns:
            Media ID pubblicato o None se errore
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.account_id}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": self.access_token
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                media_id = data.get('id')
                logger.info(f"Media pubblicato: {media_id}")
                return media_id
                
        except Exception as e:
            logger.error(f"Errore pubblicazione: {e}")
            return None
    
    async def publish_photo(self, image_url: str, caption: str = "") -> dict:
        """
        Workflow completo: crea container + pubblica
        
        Args:
            image_url: URL pubblico immagine
            caption: Didascalia post
        
        Returns:
            Dict con risultato: {success, container_id, media_id, error}
        """
        result = {
            'success': False,
            'container_id': None,
            'media_id': None,
            'error': None
        }
        
        # Step 1: Crea container
        container_id = await self.create_container(image_url, caption)
        if not container_id:
            result['error'] = "Errore creazione container"
            return result
        
        result['container_id'] = container_id
        
        # Attendi processing (Instagram richiede 5-30 secondi)
        logger.info("Attendo processing container...")
        await asyncio.sleep(10)
        
        # Step 2: Pubblica
        media_id = await self.publish_container(container_id)
        if not media_id:
            result['error'] = "Errore pubblicazione container"
            return result
        
        result['media_id'] = media_id
        result['success'] = True
        
        return result
    
    async def get_account_info(self) -> Optional[dict]:
        """Ottieni info account Instagram"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/{self.account_id}",
                    params={
                        "fields": "username,name,profile_picture_url,followers_count,follows_count,media_count",
                        "access_token": self.access_token
                    }
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as he:
                    # Log full response body for easier debugging (Graph API returns JSON with message)
                    text = None
                    try:
                        text = response.text
                    except Exception:
                        text = '<no response body available>'
                    logger.error(f"Errore info account: HTTP {response.status_code} - {text}")
                    return None

                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Errore info account (request): {e}")
            return None
        except Exception as e:
            logger.error(f"Errore info account: {e}")
            return None


if __name__ == "__main__":
    # Test
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        publisher = InstagramPublisher(
            access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
            account_id=os.getenv('INSTAGRAM_ACCOUNT_ID', '')
        )
        
        # Test info account
        info = await publisher.get_account_info()
        if info:
            print(f"✅ Account: @{info.get('username')}")
            print(f"   Followers: {info.get('followers_count')}")
        else:
            print("❌ Errore connessione Instagram")
    
    asyncio.run(test())
