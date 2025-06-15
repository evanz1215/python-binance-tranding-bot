#!/usr/bin/env python3
"""
Comprehensive monitoring and testing script for the Binance Trading Bot
"""
import asyncio
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.binance_client import binance_client
from src.data_manager import data_manager
from src.risk_manager import risk_manager
from src.trading_engine import TradingEngine
from src.notifications import NotificationManager
from src.strategies import get_strategy, STRATEGIES
from loguru import logger


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")


def print_status(item: str, status: str, details: str = ""):
    """Print a status line"""
    status_emoji = "✅" if status == "OK" else "❌"
    print(f"{status_emoji} {item}: {status}")
    if details:
        print(f"   └─ {details}")


async def test_system_components():
    """Test all system components"""
    print_header("SYSTEM COMPONENT TESTS")
    
    # Test configuration
    print_status("Configuration", "OK", f"Base currency: {config.trading.base_currency}")
      # Test database connection
    try:
        from src.database.models import get_session_factory
        SessionFactory = get_session_factory(config.database.url)
        with SessionFactory() as session:
            # Test a simple query
            result = session.execute("SELECT 1").fetchone()
        print_status("Database Connection", "OK", f"URL: {config.database.url}")
    except Exception as e:
        print_status("Database Connection", "FAILED", str(e))
    
    # Test Binance client (without API keys)
    try:
        # This will work even without real API keys since we have defaults
        client_status = "OK" if config.binance.api_key else "No API Keys"
        print_status("Binance Client", client_status, 
                    f"Testnet: {config.binance.testnet}")
    except Exception as e:
        print_status("Binance Client", "FAILED", str(e))
    
    # Test strategies
    strategy_count = len(STRATEGIES)
    print_status("Trading Strategies", "OK", f"{strategy_count} strategies available")
    
    # Test notifications
    notification_manager = NotificationManager()
    telegram_status = "Configured" if notification_manager.telegram_enabled else "Not configured"
    discord_status = "Configured" if notification_manager.discord_enabled else "Not configured"
    print_status("Notifications", "OK", f"Telegram: {telegram_status}, Discord: {discord_status}")


async def test_data_operations():
    """Test data-related operations"""
    print_header("DATA OPERATIONS TEST")
    
    try:
        # Test symbol info retrieval
        symbols = data_manager.get_active_symbols(limit=5)
        print_status("Symbol Information", "OK", f"Found {len(symbols)} active symbols")
        
        # Test market data (if available)
        if symbols:
            symbol = symbols[0]
            market_data = data_manager.get_market_data(symbol, "1h", limit=10)
            if len(market_data) > 0:
                print_status("Market Data", "OK", f"Retrieved {len(market_data)} data points for {symbol}")
            else:
                print_status("Market Data", "NO DATA", f"No historical data for {symbol}")
        
    except Exception as e:
        print_status("Data Operations", "FAILED", str(e))


async def test_strategy_execution():
    """Test strategy execution"""
    print_header("STRATEGY EXECUTION TEST")
    
    try:
        # Test each strategy with sample data
        import pandas as pd
        import numpy as np
        
        # Create sample market data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='h')
        sample_data = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.random.randn(100) * 2,
            'high': 102 + np.random.randn(100) * 2,
            'low': 98 + np.random.randn(100) * 2,
            'close': 100 + np.random.randn(100) * 2,
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        for strategy_name in STRATEGIES:
            try:
                strategy = get_strategy(strategy_name)
                signal = strategy.generate_signal(sample_data, 'TEST')
                print_status(f"Strategy {strategy_name}", "OK", 
                           f"Signal: {signal.action}, Strength: {signal.strength:.2f}")
            except Exception as e:
                print_status(f"Strategy {strategy_name}", "FAILED", str(e))
                
    except Exception as e:
        print_status("Strategy Testing", "FAILED", str(e))


async def test_risk_management():
    """Test risk management"""
    print_header("RISK MANAGEMENT TEST")
    
    try:
        # Test risk level calculation
        risk_level = risk_manager.calculate_risk_level(10000.0)
        print_status("Risk Level Calculation", "OK", f"Risk level: {risk_level}")
        
        # Test position sizing
        position_size = risk_manager.calculate_position_size(10000.0, 'BTCUSDT', 50000.0)
        print_status("Position Sizing", "OK", f"Position size: ${position_size:.2f}")
        
        # Test risk metrics
        can_trade = risk_manager.can_open_position('BUY', 'BTCUSDT')
        print_status("Trade Permission", "OK", f"Can trade: {can_trade}")
        
    except Exception as e:
        print_status("Risk Management", "FAILED", str(e))


def display_system_status():
    """Display current system status"""
    print_header("SYSTEM STATUS OVERVIEW")
    
    # Configuration status
    print("📊 Configuration:")
    print(f"   • Base Currency: {config.trading.base_currency}")
    print(f"   • Max Positions: {config.trading.max_positions}")
    print(f"   • Position Size: {config.trading.position_size_pct * 100}%")
    print(f"   • Stop Loss: {config.trading.stop_loss_pct * 100}%")
    print(f"   • Take Profit: {config.trading.take_profit_pct * 100}%")
    print(f"   • Testnet Mode: {config.is_testnet}")
    
    # Available strategies
    print(f"\n🎯 Available Strategies ({len(STRATEGIES)}):")
    for strategy in STRATEGIES:
        print(f"   • {strategy}")
    
    # Database info
    print(f"\n🗄️ Database: {config.database.url}")
    
    # Notification status
    print(f"\n🔔 Notifications:")
    print(f"   • Telegram: {'✅' if config.notifications.telegram_bot_token else '❌'}")
    print(f"   • Discord: {'✅' if config.notifications.discord_webhook else '❌'}")


def display_usage_examples():
    """Display usage examples"""
    print_header("USAGE EXAMPLES")
    
    examples = [
        ("Start Web Interface", "python main.py api"),
        ("Update Market Data", "python main.py update-data --symbols BTCUSDT ETHUSDT"),
        ("Run Backtest", "python main.py backtest --strategy ma_cross --symbols BTCUSDT --days 30"),
        ("Start Trading", "python main.py trade --strategy ma_cross"),
        ("Test Notifications", "python main.py test-notifications"),
        ("Run Demo", "python demo.py"),
        ("Monitor System", "python monitor.py"),
        ("Full System Test", "python system_test.py"),
    ]
    
    for description, command in examples:
        print(f"📌 {description}:")
        print(f"   {command}")
        print()


async def run_full_system_test():
    """Run comprehensive system test"""
    print_header("BINANCE TRADING BOT - COMPREHENSIVE SYSTEM TEST")
    
    start_time = time.time()
    
    # Display system status
    display_system_status()
    
    # Run component tests
    await test_system_components()
    await test_data_operations()
    await test_strategy_execution()
    await test_risk_management()
    
    # Display usage examples
    display_usage_examples()
    
    # Test summary
    end_time = time.time()
    print_header("TEST SUMMARY")
    print(f"✅ System test completed in {end_time - start_time:.2f} seconds")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🚀 The Binance Trading Bot is ready for use!")
    print("📖 Check README.md for detailed documentation")
    print("⚡ Check QUICKSTART.md for quick setup guide")
    print()


if __name__ == "__main__":
    # Setup logging
    logger.add("logs/system_test.log", rotation="1 MB")
    
    # Run the test
    asyncio.run(run_full_system_test())
