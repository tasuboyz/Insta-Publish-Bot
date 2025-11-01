"""
Configurazione centralizzata per il bot Telegram
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()


@dataclass
class BotConfig:
    """Configurazione Telegram Bot"""
    token: str
    use_webhook: bool
    webhook_url: str | None
    webhook_path: str
    web_app_host: str
    web_app_port: int
    
    @classmethod
    def from_env(cls):
        """Crea configurazione da variabili d'ambiente"""
        return cls(
            token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            use_webhook=os.getenv('USE_WEBHOOK', 'false').lower() == 'true',
            webhook_url=os.getenv('WEBHOOK_URL'),
            webhook_path=os.getenv('WEBHOOK_PATH', '/webhook'),
            web_app_host=os.getenv('WEB_APP_HOST', '0.0.0.0'),
            web_app_port=int(os.getenv('WEB_APP_PORT', '8080'))
        )


@dataclass
class SteemConfig:
    """Configurazione Steem blockchain"""
    username: str
    wif: str
    nodes: list[str]
    auto_find_fastest: bool = True  # Abilita ricerca automatica nodo più veloce
    
    @classmethod
    def from_env(cls):
        """Crea configurazione da variabili d'ambiente"""
        nodes_str = os.getenv('STEEM_NODES', 'https://api.steemit.com,https://api.steemdb.com')
        return cls(
            username=os.getenv('STEEM_USERNAME', ''),
            wif=os.getenv('STEEM_WIF', ''),
            nodes=[node.strip() for node in nodes_str.split(',')],
            auto_find_fastest=os.getenv('STEEM_AUTO_FIND_FASTEST', 'true').lower() == 'true'
        )


@dataclass
class InstagramConfig:
    """Configurazione Instagram Graph API"""
    access_token: str
    account_id: str
    graph_api_version: str
    app_id: str | None = None
    app_secret: str | None = None
    auto_refresh_token: bool = False  # Disabilitato per default a causa di problemi configurazione app
    
    @classmethod
    def from_env(cls):
        """Crea configurazione da variabili d'ambiente"""
        return cls(
            access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
            account_id=os.getenv('INSTAGRAM_ACCOUNT_ID', ''),
            graph_api_version=os.getenv('FACEBOOK_GRAPH_API_VERSION', 'v23.0'),
            app_id=os.getenv('FACEBOOK_APP_ID'),
            app_secret=os.getenv('FACEBOOK_APP_SECRET'),
            auto_refresh_token=os.getenv('AUTO_REFRESH_TOKEN', 'false').lower() == 'true'
        )


@dataclass
class AppConfig:
    """Configurazione completa dell'applicazione"""
    bot: BotConfig
    steem: SteemConfig
    instagram: InstagramConfig
    temp_dir: str
    log_level: str
    
    @classmethod
    def from_env(cls):
        """Crea configurazione completa da variabili d'ambiente"""
        return cls(
            bot=BotConfig.from_env(),
            steem=SteemConfig.from_env(),
            instagram=InstagramConfig.from_env(),
            temp_dir=os.getenv('TEMP_DIR', 'temp'),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
    
    def validate(self) -> list[str]:
        """Valida la configurazione e restituisce lista di errori"""
        errors = []
        
        if not self.bot.token:
            errors.append("TELEGRAM_BOT_TOKEN non configurato")
        
        if not self.steem.username:
            errors.append("STEEM_USERNAME non configurato")
        
        if not self.steem.wif:
            errors.append("STEEM_WIF non configurato")
        
        # Instagram token is optional if app_id/secret are set (token_manager can generate it)
        if not self.instagram.access_token:
            if not self.instagram.app_id or not self.instagram.app_secret:
                errors.append("INSTAGRAM_ACCESS_TOKEN non configurato (oppure configura FACEBOOK_APP_ID e FACEBOOK_APP_SECRET per generarlo automaticamente)")
        
        if not self.instagram.account_id:
            errors.append("INSTAGRAM_ACCOUNT_ID non configurato")
        
        if self.bot.use_webhook and not self.bot.webhook_url:
            errors.append("USE_WEBHOOK=true ma WEBHOOK_URL non configurato")
        
        return errors


# Configurazione globale
config = AppConfig.from_env()
