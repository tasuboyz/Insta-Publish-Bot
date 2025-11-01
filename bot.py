"""
Bot Telegram per pubblicazione automatica su Instagram
Supporta modalità Webhook e Polling
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import config
from handlers import commands_router, photo_router, calendar_router
from services import token_manager
from services.scheduler import scheduler
from services.instagram_publisher_async import InstagramPublisher

# Configurazione logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def publish_scheduled_posts(bot: Bot):
    """
    Task in background per pubblicare i post programmati
    """
    logger.info("🚀 Avvio task pubblicazione post programmati")
    
    while True:
        try:
            # Controlla ogni minuto se ci sono post da pubblicare
            await asyncio.sleep(60)  # 60 secondi
            
            # Crea istanza Instagram publisher
            instagram = InstagramPublisher(
                access_token=config.instagram.access_token,
                account_id=config.instagram.account_id,
                api_version=config.instagram.graph_api_version
            )
            
            # Pubblica post scaduti
            await scheduler.publish_due_posts(instagram)
            
        except Exception as e:
            logger.error(f"Errore nel task scheduler: {e}")
            await asyncio.sleep(30)  # Aspetta 30 secondi prima di riprovare


async def on_startup(bot: Bot) -> None:
    """Callback eseguito all'avvio del bot"""
    logger.info("🚀 Bot avviato!")
    
    # Valida configurazione
    errors = config.validate()
    if errors:
        logger.error("⚠️ Errori configurazione:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.warning("Il bot potrebbe non funzionare correttamente")
    
    # Se webhook mode, imposta webhook
    if config.bot.use_webhook:
        webhook_url = f"{config.bot.webhook_url}{config.bot.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"🌐 Webhook impostato: {webhook_url}")
    else:
        # In polling mode, rimuovi eventuali webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("📡 Modalità Polling attivata")
    
    # Info bot
    bot_info = await bot.get_me()
    logger.info(f"🤖 Bot: @{bot_info.username} (ID: {bot_info.id})")
    # Start token refresh background task if possible
    if config.instagram.auto_refresh_token:
        try:
            # create task and attach to bot object so we can cancel on shutdown
            bot._token_refresh_task = token_manager.start_background_task()
            logger.info("Started token refresh background task")
        except Exception:
            logger.debug("Token refresh task not started")
    else:
        logger.info("Token auto-refresh disabled (AUTO_REFRESH_TOKEN=false)")
    
    # Start scheduled posts publishing task
    try:
        bot._scheduler_task = asyncio.create_task(publish_scheduled_posts(bot))
        logger.info("Started scheduled posts publishing task")
    except Exception as e:
        logger.debug(f"Scheduler task not started: {e}")


async def on_shutdown(bot: Bot) -> None:
    """Callback eseguito allo shutdown del bot"""
    logger.info("👋 Shutdown bot...")
    
    if config.bot.use_webhook:
        await bot.delete_webhook()
        logger.info("Webhook rimosso")
    # cancel token refresh task
    try:
        task = getattr(bot, '_token_refresh_task', None)
        if task:
            task.cancel()
            await task
            logger.info("Token refresh background task stopped")
    except Exception:
        logger.debug("Error stopping token refresh task")
    
    # cancel scheduler task
    try:
        task = getattr(bot, '_scheduler_task', None)
        if task:
            task.cancel()
            await task
            logger.info("Scheduler background task stopped")
    except Exception:
        logger.debug("Error stopping scheduler task")


async def main_polling():
    """Avvia bot in modalità Polling"""
    # Inizializza bot e dispatcher
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Registra router (ordine importante!)
    dp.include_router(commands_router)
    dp.include_router(calendar_router)  # Prima di photo_router
    dp.include_router(photo_router)      # Ultimo perché ha catch-all handler
    
    # Registra startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Avvia polling
    logger.info("🔄 Avvio polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main_webhook():
    """Avvia bot in modalità Webhook"""
    # Inizializza bot e dispatcher
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Registra router (ordine importante!)
    dp.include_router(commands_router)
    dp.include_router(calendar_router)  # Prima di photo_router
    dp.include_router(photo_router)      # Ultimo perché ha catch-all handler
    
    # Registra startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Crea app aiohttp
    app = web.Application()
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path=config.bot.webhook_path)
    
    # Setup applicazione
    setup_application(app, dp, bot=bot)
    
    # Health check endpoint
    async def health(request):
        return web.json_response({'status': 'ok', 'bot': 'running'})
    
    app.router.add_get('/health', health)
    
    # Avvia server
    logger.info(f"🌐 Avvio webhook server su {config.bot.web_app_host}:{config.bot.web_app_port}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        config.bot.web_app_host,
        config.bot.web_app_port
    )
    await site.start()
    
    logger.info(f"✅ Server avviato: http://{config.bot.web_app_host}:{config.bot.web_app_port}")
    logger.info(f"✅ Webhook path: {config.bot.webhook_path}")
    logger.info(f"✅ Health check: http://{config.bot.web_app_host}:{config.bot.web_app_port}/health")
    
    # Mantieni il server attivo
    await asyncio.Event().wait()


def main():
    """Entry point"""
    try:
        if config.bot.use_webhook:
            logger.info("🌐 Modalità: WEBHOOK")
            asyncio.run(main_webhook())
        else:
            logger.info("📡 Modalità: POLLING")
            asyncio.run(main_polling())
    except KeyboardInterrupt:
        logger.info("⚠️ Interruzione da tastiera")
    except Exception as e:
        logger.error(f"❌ Errore fatale: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
