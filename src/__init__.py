"""
Binance Trading Bot Package
"""
__version__ = "1.0.0"
__author__ = "Trading Bot Team"
__description__ = "Automated Binance trading bot with multiple strategies and backtesting"

from .config import config
from .binance_client import BinanceClient, binance_client
from .data_manager_fixed import data_manager
from .risk_manager import risk_manager
from .trading_engine import TradingEngine
from .backtest_engine import backtest_engine
from .notifications import notification_manager

__all__ = [
    'config',
    'binance_client', 
    'data_manager',
    'risk_manager',
    'TradingEngine',
    'backtest_engine',
    'notification_manager'
]
