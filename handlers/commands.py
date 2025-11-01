"""
Handlers per comandi bot Telegram
"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import config

logger = logging.getLogger(__name__)

# Router per i comandi
commands_router = Router()


@commands_router.message(Command("start"))
async def cmd_start(message: Message):
    """Handler per comando /start"""
    welcome_text = (
        "🤖 <b>Bot Instagram Publisher</b>\n\n"
        "📸 Invia una foto con caption e la pubblicherò automaticamente su Instagram!\n\n"
        "<b>Come funziona:</b>\n"
        "1. Invia una foto nella chat\n"
        "2. Aggiungi una caption (opzionale)\n"
        "3. Aspetta mentre pubblico su Instagram\n"
        "4. Riceverai il link del post pubblicato\n\n"
        "<b>Comandi disponibili:</b>\n"
        "/start - Mostra questo messaggio\n"
        "/help - Guida completa\n"
        "/status - Stato servizi\n"
        "/settings - Impostazioni bot\n"
        "/schedule - Programma un post\n"
        "/scheduled - Gestisci post programmati\n"
        "/refresh_token - Aggiorna token Instagram\n"
        "/generate_token - Genera nuovo token Instagram"
    )
    
    await message.answer(welcome_text, parse_mode="HTML")


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handler per comando /help"""
    help_text = (
        "📖 <b>Guida Completa</b>\n\n"
        "<b>🖼 Inviare una foto:</b>\n"
        "• Invia una foto come documento o foto compressa\n"
        "• Aggiungi caption per includere testo nel post\n"
        "• Il bot scaricherà, caricherà su blockchain e pubblicherà su Instagram\n\n"
        "<b>⏰ Programmazione Post:</b>\n"
        "• /schedule - Seleziona data e ora per programmare un post\n"
        "• /scheduled - Visualizza e gestisci i post programmati\n"
        "• Invia una foto dopo aver selezionato data/ora\n\n"
        "<b>🔑 Gestione Token:</b>\n"
        "• /refresh_token - Forza aggiornamento token Instagram\n"
        "• /generate_token - Genera nuovo token via OAuth\n\n"
        "<b>⚡️ Workflow:</b>\n"
        "1. <code>Download</code> - Scarico foto da Telegram\n"
        "2. <code>Upload Blockchain</code> - Carico su Steem\n"
        "3. <code>Instagram</code> - Pubblico su Instagram\n"
        "4. <code>Notifica</code> - Ti invio link post\n\n"
        "<b>⏱ Tempo medio: 15-30 secondi</b>\n\n"
        "Hai problemi? Contatta @admin"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@commands_router.message(Command("status"))
async def cmd_status(message: Message):
    """Handler per comando /status - mostra stato servizi"""
    from services.steem_uploader import SteemUploader
    from services.instagram_publisher_async import InstagramPublisher
    from services.token_manager import debug_token
    import time
    
    status_msg = await message.answer("🔍 Verifico stato servizi...")
    
    status_text = "📊 <b>Stato Servizi</b>\n\n"
    
    # Test Steem
    try:
        steem = SteemUploader(
            username=config.steem.username,
            wif=config.steem.wif,
            nodes=config.steem.nodes,
            auto_find_fastest=config.steem.auto_find_fastest
        )
        steem_ok = await steem.test_connection()
        status_text += f"🔗 Steem: {'✅ Online' if steem_ok else '❌ Offline'}\n"
    except Exception as e:
        status_text += f"🔗 Steem: ❌ Errore ({str(e)[:50]})\n"
    
    # Test Instagram
    try:
        instagram = InstagramPublisher(
            access_token=config.instagram.access_token,
            account_id=config.instagram.account_id
        )
        ig_info = await instagram.get_account_info()
        if ig_info:
            status_text += f"📸 Instagram: ✅ @{ig_info.get('username')}\n"
            status_text += f"   Followers: {ig_info.get('followers_count', 0)}\n"
            status_text += f"   Posts: {ig_info.get('media_count', 0)}\n"
        else:
            status_text += "📸 Instagram: ❌ Errore connessione\n"
    except Exception as e:
        status_text += f"📸 Instagram: ❌ Errore ({str(e)[:50]})\n"
    
    # Token status
    try:
        token_debug = await debug_token(config.instagram.access_token)
        if token_debug:
            expires_at = token_debug.get('expires_at')
            if expires_at:
                now = int(time.time())
                seconds_left = expires_at - now
                hours_left = seconds_left // 3600
                days_left = hours_left // 24
                if days_left > 0:
                    status_text += f"🔑 Token: ✅ Scade tra {days_left} giorni\n"
                elif hours_left > 0:
                    status_text += f"🔑 Token: ⚠️ Scade tra {hours_left} ore\n"
                else:
                    status_text += f"🔑 Token: ❌ Scaduto\n"
            else:
                status_text += f"🔑 Token: ✅ Non scade\n"
        else:
            status_text += f"🔑 Token: ❓ Stato sconosciuto\n"
    except Exception as e:
        status_text += f"🔑 Token: ❓ Errore controllo\n"
    
    # Info bot
    mode = "Webhook" if config.bot.use_webhook else "Polling"
    status_text += f"\n🤖 Modalità: {mode}\n"
    status_text += f"📁 Temp dir: {config.temp_dir}\n"
    status_text += f"📝 Log level: {config.log_level}"
    
    await status_msg.edit_text(status_text, parse_mode="HTML")


@commands_router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Handler per comando /settings"""
    settings_text = (
        "⚙️ <b>Impostazioni Bot</b>\n\n"
        f"<b>Modalità:</b> {'Webhook' if config.bot.use_webhook else 'Polling'}\n"
        f"<b>Instagram Account:</b> {config.instagram.account_id}\n"
        f"<b>Steem Username:</b> {config.steem.username}\n"
        f"<b>Log Level:</b> {config.log_level}\n\n"
        "<i>Per modificare le impostazioni, edita il file .env e riavvia il bot.</i>"
    )
    
    await message.answer(settings_text, parse_mode="HTML")


@commands_router.message(Command("scheduled"))
async def cmd_scheduled(message: Message):
    """Handler per comando /scheduled - visualizza post programmati"""
    from services.scheduler import scheduler
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    user_id = message.from_user.id
    posts = scheduler.get_user_posts(user_id)

    if not posts:
        await message.answer("📭 Non hai post programmati")
        return

    text = "📅 <b>I tuoi post programmati:</b>\n\n"

    for post in posts:
        status_emoji = {
            'scheduled': '⏰',
            'published': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(post.get('status'), '❓')

        scheduled_str = post['scheduled_time'].strftime('%d/%m/%Y %H:%M')
        text += f"{status_emoji} {scheduled_str}\n"

        if post.get('status') == 'published' and post.get('instagram_media_id'):
            text += f"   📸 Media ID: {post['instagram_media_id']}\n"
        elif post.get('status') == 'failed' and post.get('error_message'):
            error_msg = post['error_message'][:50]
            text += f"   ❌ Errore: {error_msg}...\n"

        text += "\n"

    # Keyboard per gestire i post
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Aggiorna", callback_data="scheduled_refresh")]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@commands_router.message(Command("refresh_token"))
async def cmd_refresh_token(message: Message):
    """Handler per comando /refresh_token - forza refresh token Instagram"""
    from services.token_manager import force_token_refresh, test_facebook_app_config
    
    status_msg = await message.answer("� Verifico configurazione app Facebook...")
    
    try:
        # Test Facebook app configuration first
        app_test = await test_facebook_app_config()
        
        if not app_test["app_configured"]:
            await status_msg.edit_text(
                "❌ <b>Configurazione App Facebook Mancante</b>\n\n"
                "Prima di aggiornare il token, configura:\n\n"
                "• <code>FACEBOOK_APP_ID</code>\n"
                "• <code>FACEBOOK_APP_SECRET</code>\n\n"
                "Nel file <code>.env</code>\n\n"
                "Oppure usa <code>/generate_token</code> per generare un nuovo token.",
                parse_mode="HTML"
            )
            return
        
        if not app_test["can_exchange_tokens"]:
            issues_text = "\n".join(f"• {issue}" for issue in app_test["issues"])
            await status_msg.edit_text(
                f"❌ <b>Problemi Configurazione App Facebook</b>\n\n"
                f"{issues_text}\n\n"
                "<b>Risoluzioni:</b>\n"
                "1. Vai su https://developers.facebook.com/apps\n"
                "2. Seleziona la tua app\n"
                "3. Assicurati che sia in <b>Live Mode</b>\n"
                "4. Aggiungi prodotto <b>Instagram Graph API</b>\n"
                "5. Configura permessi appropriati\n\n"
                "Oppure usa <code>/generate_token</code> per generare un nuovo token.",
                parse_mode="HTML"
            )
            return
        
        # If app config looks good, try token refresh
        await status_msg.edit_text("🔄 Tentativo di aggiornamento token Instagram...")
        
        success = await force_token_refresh()
        if success:
            await status_msg.edit_text(
                "✅ <b>Token Instagram aggiornato con successo!</b>\n\n"
                "Il nuovo token è stato salvato nel file .env e sarà utilizzato per le prossime pubblicazioni.",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                "❌ <b>Impossibile aggiornare il token</b>\n\n"
                "Possibili cause:\n"
                "• Token corrente non valido/scaduto\n"
                "• Problemi di rete\n"
                "• Limiti API raggiunti\n\n"
                "Prova con <code>/generate_token</code> per generare un nuovo token.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error in refresh_token command: {e}")
        await status_msg.edit_text(
            f"❌ <b>Errore durante l'aggiornamento</b>\n\n"
            f"Dettagli: {str(e)}",
            parse_mode="HTML"
        )


@commands_router.message(Command("generate_token"))
async def cmd_generate_token(message: Message):
    """Handler per comando /generate_token - genera nuovo token via OAuth"""
    import subprocess
    import sys
    
    await message.answer(
        "🔐 <b>Generazione Nuovo Token Instagram</b>\n\n"
        "Sto avviando il processo OAuth...\n\n"
        "Segui le istruzioni che appariranno per generare un nuovo token.",
        parse_mode="HTML"
    )
    
    try:
        # Run the OAuth token generation script
        result = subprocess.run([
            sys.executable, "generate_token_oauth.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            await message.answer(
                "✅ <b>Token generato con successo!</b>\n\n"
                "Il nuovo token è stato salvato nel file .env\n"
                "Riavvia il bot per utilizzare il nuovo token.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Errore nella generazione del token</b>\n\n"
                f"<code>{result.stderr}</code>\n\n"
                "Controlla la configurazione dell'app Facebook e riprova.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error running token generation: {e}")
        await message.answer(
            f"❌ <b>Errore nell'avvio del processo</b>\n\n"
            f"Dettagli: {str(e)}",
            parse_mode="HTML"
        )
