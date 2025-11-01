"""
Servizio database SQLite per gestione sessioni utente e post programmati
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class Database:
    """Gestore database SQLite"""

    def __init__(self, db_path: str = "bot_data.db"):
        """
        Inizializza database

        Args:
            db_path: Percorso file database
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inizializza schema database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tabella sessioni utente (per programmazione post)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        user_id INTEGER PRIMARY KEY,
                        scheduled_datetime TEXT,
                        selected_date TEXT,
                        selected_hour INTEGER,
                        selected_minute INTEGER,
                        last_updated TEXT,
                        extra_data TEXT
                    )
                """)

                # Tabella post programmati
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scheduled_posts (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        image_url TEXT NOT NULL,
                        caption TEXT,
                        scheduled_time TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        status TEXT DEFAULT 'scheduled',
                        telegram_message_id INTEGER,
                        instagram_media_id TEXT,
                        error_message TEXT,
                        FOREIGN KEY (user_id) REFERENCES user_sessions(user_id)
                    )
                """)

                # Indici per performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scheduled_posts_user_id 
                    ON scheduled_posts(user_id)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status 
                    ON scheduled_posts(status)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_scheduled_posts_time 
                    ON scheduled_posts(scheduled_time)
                """)

                conn.commit()
                logger.info(f"Database inizializzato: {self.db_path}")

        except Exception as e:
            logger.error(f"Errore inizializzazione database: {e}")
            raise

    # ==================== USER SESSIONS ====================

    def save_user_session(self, user_id: int, **kwargs):
        """
        Salva o aggiorna sessione utente

        Args:
            user_id: ID utente Telegram
            **kwargs: Dati da salvare (scheduled_datetime, selected_date, etc.)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Converti datetime in ISO string se presente
                data = kwargs.copy()
                for key in ['scheduled_datetime', 'selected_date']:
                    if key in data and isinstance(data[key], datetime):
                        data[key] = data[key].isoformat()

                # Converti extra_data in JSON se presente
                if 'extra_data' in data and isinstance(data[key], dict):
                    data['extra_data'] = json.dumps(data['extra_data'])

                data['last_updated'] = datetime.now().isoformat()

                # Inserisci o aggiorna
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                values = list(data.values())

                cursor.execute(f"""
                    INSERT INTO user_sessions (user_id, {columns})
                    VALUES (?, {placeholders})
                    ON CONFLICT(user_id) DO UPDATE SET
                    {', '.join([f"{k}=excluded.{k}" for k in data.keys()])}
                """, [user_id] + values)

                conn.commit()
                logger.debug(f"Sessione utente {user_id} salvata")

        except Exception as e:
            logger.error(f"Errore salvataggio sessione utente {user_id}: {e}")
            raise

    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera sessione utente

        Args:
            user_id: ID utente Telegram

        Returns:
            Dizionario con dati sessione o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM user_sessions WHERE user_id = ?
                """, (user_id,))

                row = cursor.fetchone()
                if row:
                    data = dict(row)

                    # Converti date ISO in datetime
                    for key in ['scheduled_datetime', 'selected_date', 'last_updated']:
                        if data.get(key):
                            try:
                                data[key] = datetime.fromisoformat(data[key])
                            except:
                                pass

                    # Converti extra_data da JSON
                    if data.get('extra_data'):
                        try:
                            data['extra_data'] = json.loads(data['extra_data'])
                        except:
                            pass

                    return data

                return None

        except Exception as e:
            logger.error(f"Errore recupero sessione utente {user_id}: {e}")
            return None

    def clear_user_session(self, user_id: int):
        """
        Cancella sessione utente

        Args:
            user_id: ID utente Telegram
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
                conn.commit()
                logger.debug(f"Sessione utente {user_id} cancellata")

        except Exception as e:
            logger.error(f"Errore cancellazione sessione utente {user_id}: {e}")

    # ==================== SCHEDULED POSTS ====================

    def create_scheduled_post(self, post_id: str, user_id: int, image_url: str,
                             caption: str, scheduled_time: datetime,
                             telegram_message_id: int = None) -> bool:
        """
        Crea nuovo post programmato

        Args:
            post_id: ID univoco post
            user_id: ID utente Telegram
            image_url: URL immagine
            caption: Caption post
            scheduled_time: Quando pubblicare
            telegram_message_id: ID messaggio Telegram

        Returns:
            True se creato con successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO scheduled_posts 
                    (id, user_id, image_url, caption, scheduled_time, created_at, 
                     telegram_message_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_id,
                    user_id,
                    image_url,
                    caption,
                    scheduled_time.isoformat(),
                    datetime.now().isoformat(),
                    telegram_message_id
                ))

                conn.commit()
                logger.info(f"Post programmato creato: {post_id}")
                return True

        except Exception as e:
            logger.error(f"Errore creazione post programmato {post_id}: {e}")
            return False

    def get_user_posts(self, user_id: int, status: str = None) -> list:
        """
        Recupera post programmati di un utente

        Args:
            user_id: ID utente Telegram
            status: Filtra per status (optional)

        Returns:
            Lista di post
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if status:
                    cursor.execute("""
                        SELECT * FROM scheduled_posts 
                        WHERE user_id = ? AND status = ?
                        ORDER BY scheduled_time ASC
                    """, (user_id, status))
                else:
                    cursor.execute("""
                        SELECT * FROM scheduled_posts 
                        WHERE user_id = ?
                        ORDER BY scheduled_time ASC
                    """, (user_id,))

                rows = cursor.fetchall()
                posts = []

                for row in rows:
                    post = dict(row)
                    # Converti date
                    if post.get('scheduled_time'):
                        post['scheduled_time'] = datetime.fromisoformat(post['scheduled_time'])
                    if post.get('created_at'):
                        post['created_at'] = datetime.fromisoformat(post['created_at'])
                    posts.append(post)

                return posts

        except Exception as e:
            logger.error(f"Errore recupero post utente {user_id}: {e}")
            return []

    def get_due_posts(self) -> list:
        """
        Recupera post da pubblicare ora

        Returns:
            Lista di post scaduti non ancora pubblicati
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                now = datetime.now().isoformat()

                cursor.execute("""
                    SELECT * FROM scheduled_posts 
                    WHERE status = 'scheduled' AND scheduled_time <= ?
                    ORDER BY scheduled_time ASC
                """, (now,))

                rows = cursor.fetchall()
                posts = []

                for row in rows:
                    post = dict(row)
                    # Converti date
                    if post.get('scheduled_time'):
                        post['scheduled_time'] = datetime.fromisoformat(post['scheduled_time'])
                    if post.get('created_at'):
                        post['created_at'] = datetime.fromisoformat(post['created_at'])
                    posts.append(post)

                return posts

        except Exception as e:
            logger.error(f"Errore recupero post scaduti: {e}")
            return []

    def update_post_status(self, post_id: str, status: str,
                          instagram_media_id: str = None,
                          error_message: str = None) -> bool:
        """
        Aggiorna stato di un post

        Args:
            post_id: ID post
            status: Nuovo status
            instagram_media_id: ID media Instagram (optional)
            error_message: Messaggio errore (optional)

        Returns:
            True se aggiornato con successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                updates = ["status = ?"]
                values = [status]

                if instagram_media_id:
                    updates.append("instagram_media_id = ?")
                    values.append(instagram_media_id)

                if error_message:
                    updates.append("error_message = ?")
                    values.append(error_message)

                values.append(post_id)

                cursor.execute(f"""
                    UPDATE scheduled_posts 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, values)

                conn.commit()
                logger.info(f"Post {post_id} aggiornato: {status}")
                return True

        except Exception as e:
            logger.error(f"Errore aggiornamento post {post_id}: {e}")
            return False

    def cancel_post(self, post_id: str, user_id: int) -> bool:
        """
        Cancella un post programmato

        Args:
            post_id: ID post
            user_id: ID utente (per verifica ownership)

        Returns:
            True se cancellato con successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE scheduled_posts 
                    SET status = 'cancelled'
                    WHERE id = ? AND user_id = ? AND status = 'scheduled'
                """, (post_id, user_id))

                rows_affected = cursor.rowcount
                conn.commit()

                if rows_affected > 0:
                    logger.info(f"Post {post_id} cancellato")
                    return True
                else:
                    logger.warning(f"Post {post_id} non trovato o già pubblicato")
                    return False

        except Exception as e:
            logger.error(f"Errore cancellazione post {post_id}: {e}")
            return False

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera un post per ID

        Args:
            post_id: ID post

        Returns:
            Dizionario con dati post o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM scheduled_posts WHERE id = ?
                """, (post_id,))

                row = cursor.fetchone()
                if row:
                    post = dict(row)
                    # Converti date
                    if post.get('scheduled_time'):
                        post['scheduled_time'] = datetime.fromisoformat(post['scheduled_time'])
                    if post.get('created_at'):
                        post['created_at'] = datetime.fromisoformat(post['created_at'])
                    return post

                return None

        except Exception as e:
            logger.error(f"Errore recupero post {post_id}: {e}")
            return None

    # ==================== UTILITY ====================

    def cleanup_old_sessions(self, days: int = 7):
        """
        Pulisce sessioni utente più vecchie di N giorni

        Args:
            days: Numero di giorni
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cutoff = datetime.now() - timedelta(days=days)

                cursor.execute("""
                    DELETE FROM user_sessions 
                    WHERE last_updated < ?
                """, (cutoff.isoformat(),))

                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"Cancellate {deleted} sessioni vecchie")

        except Exception as e:
            logger.error(f"Errore pulizia sessioni: {e}")

    def cleanup_old_posts(self, days: int = 30):
        """
        Pulisce post vecchi già pubblicati/falliti

        Args:
            days: Numero di giorni
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cutoff = datetime.now() - timedelta(days=days)

                cursor.execute("""
                    DELETE FROM scheduled_posts 
                    WHERE created_at < ? 
                    AND status IN ('published', 'failed', 'cancelled')
                """, (cutoff.isoformat(),))

                deleted = cursor.rowcount
                conn.commit()

                if deleted > 0:
                    logger.info(f"Cancellati {deleted} post vecchi")

        except Exception as e:
            logger.error(f"Errore pulizia post: {e}")

    def get_stats(self) -> Dict[str, int]:
        """
        Ottieni statistiche database

        Returns:
            Dizionario con statistiche
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Conta sessioni attive
                cursor.execute("SELECT COUNT(*) FROM user_sessions")
                stats['active_sessions'] = cursor.fetchone()[0]

                # Conta post per status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM scheduled_posts 
                    GROUP BY status
                """)
                for status, count in cursor.fetchall():
                    stats[f'posts_{status}'] = count

                return stats

        except Exception as e:
            logger.error(f"Errore recupero statistiche: {e}")
            return {}


# Istanza globale database
db = Database()


if __name__ == "__main__":
    # Test database
    print("🧪 Test Database SQLite\n")

    # Test user session
    print("1️⃣ Test User Session...")
    db.save_user_session(
        user_id=123456,
        scheduled_datetime=datetime.now(),
        selected_hour=14,
        selected_minute=30
    )
    session = db.get_user_session(123456)
    print(f"✅ Sessione salvata: {session}")

    # Test scheduled post
    print("\n2️⃣ Test Scheduled Post...")
    post_id = "test_post_123"
    db.create_scheduled_post(
        post_id=post_id,
        user_id=123456,
        image_url="https://example.com/image.jpg",
        caption="Test caption",
        scheduled_time=datetime.now(),
        telegram_message_id=789
    )
    print(f"✅ Post creato: {post_id}")

    # Get user posts
    posts = db.get_user_posts(123456)
    print(f"✅ Post utente: {len(posts)}")

    # Update status
    db.update_post_status(post_id, "published", instagram_media_id="IG123")
    print(f"✅ Status aggiornato")

    # Stats
    print("\n3️⃣ Statistiche:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Test completati!")
