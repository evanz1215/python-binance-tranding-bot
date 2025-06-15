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
    """Binance API configuration with support for separate spot and futures keys"""
    
    def __init__(self):
        # 現貨交易 API 金鑰
        self.spot_api_key: str = os.getenv("BINANCE_SPOT_API_KEY", "")
        self.spot_secret_key: str = os.getenv("BINANCE_SPOT_SECRET_KEY", "")
        
        # 合約交易 API 金鑰
        self.futures_api_key: str = os.getenv("BINANCE_FUTURES_API_KEY", "")
        self.futures_secret_key: str = os.getenv("BINANCE_FUTURES_SECRET_KEY", "")
        
        # 向後兼容：如果沒有設定分別的金鑰，使用通用金鑰
        fallback_api_key = os.getenv("BINANCE_API_KEY", "")
        fallback_secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        
        if not self.spot_api_key and fallback_api_key:
            self.spot_api_key = fallback_api_key
        if not self.spot_secret_key and fallback_secret_key:
            self.spot_secret_key = fallback_secret_key
            
        if not self.futures_api_key and fallback_api_key:
            self.futures_api_key = fallback_api_key
        if not self.futures_secret_key and fallback_secret_key:
            self.futures_secret_key = fallback_secret_key
        
        # 其他設定
        self.testnet: bool = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        self.demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
        self.paper_trading: bool = os.getenv("PAPER_TRADING", "false").lower() == "true"
        self.base_url: Optional[str] = os.getenv("BINANCE_BASE_URL")
        self.trading_mode: str = os.getenv("TRADING_MODE", "futures").lower()  # spot, futures, both
        
        # 時間同步設定
        self.time_offset: int = int(os.getenv("BINANCE_TIME_OFFSET", "0"))
        
    def get_api_credentials(self, trading_type: str = "futures"):
        """獲取指定交易類型的 API 憑證"""
        if trading_type.lower() == "spot":
            return self.spot_api_key, self.spot_secret_key
        elif trading_type.lower() == "futures":
            return self.futures_api_key, self.futures_secret_key
        else:
            raise ValueError(f"Unsupported trading type: {trading_type}")
    
    def has_valid_credentials(self, trading_type: str = "futures") -> bool:
        """檢查指定交易類型是否有有效的憑證"""
        api_key, secret_key = self.get_api_credentials(trading_type)
        return bool(api_key and secret_key)
    
    @property
    def api_key(self) -> str:
        """向後兼容屬性"""
        return self.futures_api_key if self.futures_api_key else self.spot_api_key
    
    @property
    def secret_key(self) -> str:
        """向後兼容屬性"""
        return self.futures_secret_key if self.futures_secret_key else self.spot_secret_key


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
        
        # 合約交易設定
        self.futures_enabled: bool = os.getenv("FUTURES_ENABLED", "false").lower() == "true"
        self.default_leverage: int = int(os.getenv("DEFAULT_LEVERAGE", "10"))
        self.max_leverage: int = int(os.getenv("MAX_LEVERAGE", "20"))
        self.margin_type: str = os.getenv("MARGIN_TYPE", "CROSSED")  # CROSSED or ISOLATED
        self.futures_commission_rate: float = float(os.getenv("FUTURES_COMMISSION_RATE", "0.0004"))  # 0.04% for futures
        
        # 合約風險管理
        self.futures_max_position_size_pct: float = float(os.getenv("FUTURES_MAX_POSITION_SIZE_PCT", "0.05"))  # 5% of balance per position
        self.futures_stop_loss_pct: float = float(os.getenv("FUTURES_STOP_LOSS_PCT", "0.03"))  # 3% stop loss
        self.futures_take_profit_pct: float = float(os.getenv("FUTURES_TAKE_PROFIT_PCT", "0.06"))  # 6% take profit


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
        
    @property
    def is_demo_mode(self) -> bool:
        return self.binance.demo_mode


# Global config instance
config = Config()
