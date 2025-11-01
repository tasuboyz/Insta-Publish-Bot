"""
Telegram Handler - Gestisce ricezione messaggi e file da Telegram
Supporta sia webhook che polling

Funzionalità:
- Ricezione messaggi Telegram (testo, foto, documenti)
- Estrazione file_id da foto
- Download file tramite Bot API
- Gestione comandi bot
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class TelegramHandler:
    """Gestisce interazioni con Telegram Bot API"""
    
    def __init__(self, bot_token: str = None):
        """
        Inizializza Telegram Handler
        
        Args:
            bot_token: Token del bot Telegram (da @BotFather)
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN non configurato")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.file_url = f"https://api.telegram.org/file/bot{self.bot_token}"
    
    def get_me(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sul bot
        
        Returns:
            dict: Info bot (id, username, first_name, etc.)
        """
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                return result["result"]
            else:
                raise Exception(f"API error: {result.get('description')}")
                
        except Exception as e:
            logger.error(f"Errore getMe: {e}")
            raise
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = None) -> Dict[str, Any]:
        """
        Invia messaggio di testo a una chat
        
        Args:
            chat_id: ID della chat destinatario
            text: Testo del messaggio
            parse_mode: Formato testo ('Markdown', 'HTML', None)
            
        Returns:
            dict: Messaggio inviato
        """
        try:
            params = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                params["parse_mode"] = parse_mode
            
            response = requests.post(f"{self.base_url}/sendMessage", json=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Messaggio inviato a {chat_id}")
                return result["result"]
            else:
                raise Exception(f"API error: {result.get('description')}")
                
        except Exception as e:
            logger.error(f"Errore invio messaggio: {e}")
            raise
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Ottiene informazioni su un file
        
        Args:
            file_id: ID del file
            
        Returns:
            dict: Info file (file_path, file_size, etc.)
        """
        try:
            params = {"file_id": file_id}
            response = requests.get(f"{self.base_url}/getFile", params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                return result["result"]
            else:
                raise Exception(f"API error: {result.get('description')}")
                
        except Exception as e:
            logger.error(f"Errore getFile: {e}")
            raise
    
    def download_file(self, file_id: str, save_path: str = None) -> str:
        """
        Scarica un file da Telegram
        
        Args:
            file_id: ID del file da scaricare
            save_path: Percorso dove salvare (opzionale)
            
        Returns:
            str: Percorso del file scaricato
        """
        try:
            # Ottieni info file
            file_info = self.get_file_info(file_id)
            file_path = file_info["file_path"]
            file_size = file_info.get("file_size", 0)
            
            logger.info(f"📥 Download file: {file_path} ({file_size} bytes)")
            
            # Download
            download_url = f"{self.file_url}/{file_path}"
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determina percorso salvataggio
            if not save_path:
                import tempfile
                from pathlib import Path
                file_ext = Path(file_path).suffix or '.jpg'
                save_path = os.path.join(tempfile.gettempdir(), f"telegram_{file_id[:10]}{file_ext}")
            
            # Salva file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ File salvato: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Errore download file: {e}")
            raise
    
    def extract_photo_file_id(self, message: Dict[str, Any], quality: str = "high") -> Optional[str]:
        """
        Estrae file_id da un messaggio con foto
        
        Args:
            message: Oggetto messaggio Telegram
            quality: Qualità foto ('low', 'medium', 'high', 'original')
            
        Returns:
            str: file_id della foto, o None se non presente
        """
        if "photo" not in message:
            return None
        
        photos = message["photo"]
        if not photos:
            return None
        
        # Telegram invia array di photo in diverse risoluzioni
        # [0] = thumb, [-1] = qualità più alta
        if quality == "high" or quality == "original":
            return photos[-1]["file_id"]  # Massima risoluzione
        elif quality == "medium":
            mid = len(photos) // 2
            return photos[mid]["file_id"]
        else:  # low
            return photos[0]["file_id"]
    
    def extract_caption(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Estrae caption da un messaggio
        
        Args:
            message: Oggetto messaggio Telegram
            
        Returns:
            str: Caption del messaggio, o None
        """
        return message.get("caption")
    
    def extract_chat_id(self, message: Dict[str, Any]) -> Optional[int]:
        """
        Estrae chat_id da un messaggio
        
        Args:
            message: Oggetto messaggio Telegram
            
        Returns:
            int: ID della chat
        """
        return message.get("chat", {}).get("id") or message.get("from", {}).get("id")
    
    def process_webhook_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa un update ricevuto via webhook
        
        Args:
            update: Oggetto update da Telegram webhook
            
        Returns:
            dict: Dati estratti (file_id, caption, chat_id, etc.)
        """
        try:
            message = update.get("message", {})
            
            result = {
                "update_id": update.get("update_id"),
                "message_id": message.get("message_id"),
                "chat_id": self.extract_chat_id(message),
                "user_id": message.get("from", {}).get("id"),
                "username": message.get("from", {}).get("username"),
                "text": message.get("text"),
                "caption": self.extract_caption(message),
                "date": message.get("date"),
                "has_photo": "photo" in message,
                "file_id": None
            }
            
            # Estrai file_id se presente foto
            if result["has_photo"]:
                result["file_id"] = self.extract_photo_file_id(message, quality="high")
                result["photo_sizes"] = len(message.get("photo", []))
            
            return result
            
        except Exception as e:
            logger.error(f"Errore processing update: {e}")
            raise
    
    def set_webhook(self, webhook_url: str, allowed_updates: List[str] = None) -> bool:
        """
        Configura webhook per ricevere update
        
        Args:
            webhook_url: URL pubblico dove ricevere webhook
            allowed_updates: Lista tipi update da ricevere (es. ['message', 'edited_message'])
            
        Returns:
            bool: True se configurato con successo
        """
        try:
            params = {"url": webhook_url}
            
            if allowed_updates:
                params["allowed_updates"] = allowed_updates
            
            response = requests.post(f"{self.base_url}/setWebhook", json=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Webhook configurato: {webhook_url}")
                return True
            else:
                raise Exception(f"API error: {result.get('description')}")
                
        except Exception as e:
            logger.error(f"Errore setWebhook: {e}")
            raise
    
    def delete_webhook(self) -> bool:
        """
        Rimuove webhook configurato
        
        Returns:
            bool: True se rimosso con successo
        """
        try:
            response = requests.post(f"{self.base_url}/deleteWebhook", timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                logger.info("✅ Webhook rimosso")
                return True
            else:
                raise Exception(f"API error: {result.get('description')}")
                
        except Exception as e:
            logger.error(f"Errore deleteWebhook: {e}")
            raise


# Esempio di utilizzo
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        handler = TelegramHandler()
        
        # Info bot
        bot_info = handler.get_me()
        print(f"🤖 Bot: @{bot_info.get('username')}")
        print(f"📝 Nome: {bot_info.get('first_name')}")
        
        # Test invio messaggio (sostituisci CHAT_ID)
        # handler.send_message(
        #     chat_id=YOUR_CHAT_ID,
        #     text="Test messaggio da Python!"
        # )
        
    except Exception as e:
        print(f"Errore: {e}")
