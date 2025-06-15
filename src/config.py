"""
Configuration management for the Binance trading bot
"""
import os
from typing import List, Optional

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv is not available, just continue
    pass


class BinanceConfig:
    """Binance API configuration"""
    
    def __init__(self):
        self.api_key: str = os.getenv("BINANCE_API_KEY", "")
        self.secret_key: str = os.getenv("BINANCE_SECRET_KEY", "")
        self.testnet: bool = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        self.base_url: Optional[str] = os.getenv("BINANCE_BASE_URL")


class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        self.url: str = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
        self.echo: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"


class RedisConfig:
    """Redis configuration"""
    
    def __init__(self):
        self.host: str = os.getenv("REDIS_HOST", "localhost")
        self.port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.db: int = int(os.getenv("REDIS_DB", "0"))
        self.password: Optional[str] = os.getenv("REDIS_PASSWORD")


class TradingConfig:
    """Trading configuration"""
    
    def __init__(self):
        self.base_currency: str = os.getenv("BASE_CURRENCY", "USDT")
        self.max_positions: int = int(os.getenv("MAX_POSITIONS", "10"))
        self.position_size_pct: float = float(os.getenv("POSITION_SIZE_PCT", "0.1"))  # 10% of balance per trade
        self.stop_loss_pct: float = float(os.getenv("STOP_LOSS_PCT", "0.05"))  # 5% stop loss
        self.take_profit_pct: float = float(os.getenv("TAKE_PROFIT_PCT", "0.15"))  # 15% take profit
        self.min_volume_24h: float = float(os.getenv("MIN_VOLUME_24H", "1000000"))  # Minimum 24h volume in USDT
        
        # Symbol filtering
        whitelist_str = os.getenv("WHITELIST", "")
        self.whitelist: List[str] = [s.strip() for s in whitelist_str.split(",") if s.strip()] if whitelist_str else []
        
        blacklist_str = os.getenv("BLACKLIST", "")
        self.blacklist: List[str] = [s.strip() for s in blacklist_str.split(",") if s.strip()] if blacklist_str else []
          # Risk management
        self.max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.10"))  # 10% max daily loss
        self.max_drawdown_pct: float = float(os.getenv("MAX_DRAWDOWN_PCT", "0.20"))  # 20% max drawdown
        
        # Trading costs
        self.commission_rate: float = float(os.getenv("COMMISSION_RATE", "0.001"))  # 0.1% commission


class NotificationConfig:
    """Notification configuration"""
    
    def __init__(self):
        self.telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
        self.discord_webhook: Optional[str] = os.getenv("DISCORD_WEBHOOK")


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.binance = BinanceConfig()
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.trading = TradingConfig()
        self.notifications = NotificationConfig()
        
    @property
    def is_testnet(self) -> bool:
        return self.binance.testnet


# Global config instance
config = Config()
