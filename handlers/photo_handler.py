"""
Handlers per foto e documenti
"""
import os
import asyncio
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, PhotoSize, Document
from aiogram.exceptions import TelegramAPIError
from config import config
from services.steem_uploader import SteemUploader
from services.instagram_publisher_async import InstagramPublisher
from services.scheduler import scheduler
from services.database import db

logger = logging.getLogger(__name__)

# Router per foto
photo_router = Router()

# Inizializza servizi
steem_uploader = SteemUploader(
    username=config.steem.username,
    wif=config.steem.wif,
    nodes=config.steem.nodes,
    auto_find_fastest=config.steem.auto_find_fastest
)

instagram_publisher = InstagramPublisher(
    access_token=config.instagram.access_token,
    account_id=config.instagram.account_id,
    api_version=config.instagram.graph_api_version
)


async def process_photo(message: Message, file_id: str, caption: str = ""):
    """
    Processa foto: download -> Steem -> Instagram (o scheduling)
    
    Args:
        message: Messaggio Telegram originale
        file_id: ID file Telegram
        caption: Caption della foto
    """
    user_id = message.from_user.id
    
    # Controlla se l'utente ha una sessione di programmazione attiva
    session = db.get_user_session(user_id)
    scheduled_datetime = None
    
    if session and session.get('scheduled_datetime'):
        scheduled_datetime = session['scheduled_datetime']
        logger.info(f"Trovato datetime programmato per utente {user_id}: {scheduled_datetime}")
    
    status_msg = await message.answer("📥 Sto scaricando la foto...")
    
    try:
        # 1. Download da Telegram
        logger.info(f"Download file {file_id}")
        bot = message.bot
        file = await bot.get_file(file_id)
        
        # Crea directory temp se non esiste
        os.makedirs(config.temp_dir, exist_ok=True)
        
        # Percorso file temporaneo
        file_ext = os.path.splitext(file.file_path)[1] or '.jpg'
        temp_path = os.path.join(config.temp_dir, f"photo_{message.message_id}{file_ext}")
        
        # Download file
        await bot.download_file(file.file_path, temp_path)
        logger.info(f"File scaricato: {temp_path}")
        
        await status_msg.edit_text("⬆️ Sto caricando su blockchain...")
        
        # 2. Upload su Steem
        logger.info("Upload su Steem")
        image_url = await steem_uploader.upload_image(temp_path)
        
        if not image_url:
            await status_msg.edit_text("❌ Errore durante l'upload su blockchain")
            return
        
        logger.info(f"Immagine caricata: {image_url}")
        
        # 3. Programma o pubblica il post
        if scheduled_datetime and scheduled_datetime > datetime.now():
            # Programma il post
            logger.info(f"Programmazione post per {scheduled_datetime}")
            await status_msg.edit_text(f"✅ Caricata su blockchain!\n\n⏰ Programmando post per {scheduled_datetime.strftime('%d/%m/%Y %H:%M')}...")
            
            post_id = scheduler.schedule_post(
                user_id=user_id,
                image_url=image_url,
                caption=caption,
                scheduled_time=scheduled_datetime,
                telegram_message_id=message.message_id
            )
            
            success_text = (
                "🎉 <b>Post programmato con successo!</b>\n\n"
                f"🔗 Blockchain: <a href='{image_url}'>Link</a>\n"
                f"🕐 Pubblicazione: {scheduled_datetime.strftime('%d/%m/%Y %H:%M')}\n"
                f"📝 Caption: {caption or '(nessuna)'}\n\n"
                f"✨ <i>Il post sarà pubblicato automaticamente all'orario programmato!</i>"
            )
            await status_msg.edit_text(success_text, parse_mode="HTML")
            
        else:
            # Pubblica immediatamente
            await status_msg.edit_text(f"✅ Caricata su blockchain!\n\n📸 Sto pubblicando su Instagram...")
            
            # 3. Pubblica su Instagram
            logger.info("Pubblicazione su Instagram")
            result = await instagram_publisher.publish_photo(image_url, caption or "")
            
            if result['success']:
                success_text = (
                    "🎉 <b>Pubblicato con successo!</b>\n\n"
                    f"🔗 Blockchain: <a href='{image_url}'>Link</a>\n"
                    f"📸 Instagram: Media ID {result['media_id']}\n\n"
                    f"✨ <i>Post pubblicato sul tuo account Instagram!</i>"
                )
                await status_msg.edit_text(success_text, parse_mode="HTML")
            else:
                error_text = (
                    f"⚠️ Immagine caricata su blockchain ma errore Instagram:\n\n"
                    f"🔗 URL: {image_url}\n"
                    f"❌ Errore: {result.get('error', 'Sconosciuto')}"
                )
                await status_msg.edit_text(error_text)
        
        # 4. Cleanup file temporaneo
        try:
            os.remove(temp_path)
            logger.info(f"File temporaneo rimosso: {temp_path}")
        except:
            pass
            
    except TelegramAPIError as e:
        logger.error(f"Errore Telegram API: {e}")
        await status_msg.edit_text(f"❌ Errore Telegram: {str(e)}")
    except Exception as e:
        logger.error(f"Errore processing foto: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Errore imprevisto: {str(e)}")


@photo_router.message(F.photo)
async def handle_photo(message: Message):
    """Handler per foto (compresse)"""
    # Prendi la foto con qualità migliore
    photo: PhotoSize = message.photo[-1]
    
    # Estrai caption
    caption = message.caption or ""
    
    logger.info(f"Ricevuta foto da {message.from_user.username}: {photo.file_id}")
    
    # Processa foto
    await process_photo(message, photo.file_id, caption)


@photo_router.message(F.document)
async def handle_document(message: Message):
    """Handler per documenti (foto non compresse)"""
    document: Document = message.document
    
    # Verifica che sia un'immagine
    mime_type = document.mime_type or ""
    if not mime_type.startswith('image/'):
        await message.answer("⚠️ Per favore invia un'immagine (JPG, PNG)")
        return
    
    # Verifica dimensione (max 20 MB)
    max_size = 20 * 1024 * 1024  # 20 MB
    if document.file_size > max_size:
        await message.answer(f"⚠️ File troppo grande (max 20 MB)")
        return
    
    # Estrai caption
    caption = message.caption or ""
    
    logger.info(f"Ricevuto documento da {message.from_user.username}: {document.file_id}")
    
    # Processa foto
    await process_photo(message, document.file_id, caption)


@photo_router.message()
async def handle_other(message: Message):
    """Handler per altri tipi di messaggi"""
    await message.answer(
        "🤔 Non ho capito...\n\n"
        "Inviami una foto con /help per vedere cosa posso fare!"
    )
