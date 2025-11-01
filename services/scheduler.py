"""
Servizio per la gestione della programmazione dei post
Usa database SQLite tramite services.database
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from services.database import db

logger = logging.getLogger(__name__)


class PostScheduler:
    """Gestore della programmazione dei post usando database SQLite"""

    def __init__(self):
        """Inizializza scheduler con database"""
        self.db = db
        logger.info("Scheduler inizializzato con database SQLite")

    def schedule_post(self, user_id: int, image_url: str, caption: str,
                     scheduled_time: datetime, telegram_message_id: int = None) -> str:
        """
        Programma un nuovo post

        Args:
            user_id: ID utente Telegram
            image_url: URL dell'immagine
            caption: Caption del post
            scheduled_time: Quando pubblicare
            telegram_message_id: ID messaggio Telegram originale

        Returns:
            ID del post programmato
        """
        post_id = f"{user_id}_{int(scheduled_time.timestamp())}_{telegram_message_id or 0}"

        success = self.db.create_scheduled_post(
            post_id=post_id,
            user_id=user_id,
            image_url=image_url,
            caption=caption,
            scheduled_time=scheduled_time,
            telegram_message_id=telegram_message_id
        )

        if success:
            logger.info(f"Post programmato: {post_id} per {scheduled_time}")
            # Pulisci sessione utente dopo aver programmato il post
            self.db.clear_user_session(user_id)
        else:
            logger.error(f"Errore programmazione post per utente {user_id}")

        return post_id

    def get_user_posts(self, user_id: int, status: str = None) -> List[Dict[str, Any]]:
        """
        Ottieni i post programmati di un utente

        Args:
            user_id: ID utente
            status: Filtra per status (optional)

        Returns:
            Lista di post
        """
        return self.db.get_user_posts(user_id, status)

    def get_due_posts(self) -> List[Dict[str, Any]]:
        """
        Ottieni i post da pubblicare ora

        Returns:
            Lista di post scaduti
        """
        return self.db.get_due_posts()

    def update_post_status(self, post_id: str, status: str,
                          instagram_media_id: str = None, error_message: str = None):
        """
        Aggiorna lo stato di un post

        Args:
            post_id: ID post
            status: Nuovo status
            instagram_media_id: ID media Instagram (optional)
            error_message: Messaggio errore (optional)
        """
        self.db.update_post_status(post_id, status, instagram_media_id, error_message)

    def cancel_post(self, post_id: str, user_id: int) -> bool:
        """
        Cancella un post programmato

        Args:
            post_id: ID post
            user_id: ID utente

        Returns:
            True se cancellato con successo
        """
        return self.db.cancel_post(post_id, user_id)

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Ottieni un post per ID

        Args:
            post_id: ID post

        Returns:
            Dizionario con dati post o None
        """
        return self.db.get_post_by_id(post_id)

    async def publish_due_posts(self, instagram_publisher):
        """
        Pubblica i post scaduti

        Args:
            instagram_publisher: Istanza di InstagramPublisher
        """
        due_posts = self.get_due_posts()

        if not due_posts:
            return

        logger.info(f"Trovati {len(due_posts)} post da pubblicare")

        for post in due_posts:
            try:
                logger.info(f"Pubblicazione post programmato: {post['id']}")

                # Pubblica su Instagram
                result = await instagram_publisher.publish_photo(
                    post['image_url'],
                    post['caption'] or ""
                )

                if result['success']:
                    self.update_post_status(
                        post['id'],
                        'published',
                        result.get('media_id')
                    )
                    logger.info(f"Post {post['id']} pubblicato con successo")
                else:
                    error_msg = result.get('error', 'Errore sconosciuto')
                    self.update_post_status(
                        post['id'],
                        'failed',
                        error_message=error_msg
                    )
                    logger.error(f"Errore pubblicazione post {post['id']}: {error_msg}")

            except Exception as e:
                logger.error(f"Errore pubblicazione post {post['id']}: {e}")
                self.update_post_status(
                    post['id'],
                    'failed',
                    error_message=str(e)
                )


# Istanza globale del scheduler
scheduler = PostScheduler()