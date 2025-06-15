"""
Binance Trading Bot - Main Entry Point
"""
import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional, List
from loguru import logger

from src.config import config
from src.trading_engine import TradingEngine
from src.backtest_engine import backtest_engine
from src.api import run_api_server
from src.data_manager import data_manager
from src.notifications import notification_manager


def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File logging
    logger.add(
        "logs/trading_bot.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )


async def run_trading_bot(strategy_name: str = "ma_cross", **strategy_params):
    """Run the trading bot"""
    try:
        logger.info("Starting Binance Trading Bot...")
        
        # Send startup notification
        await notification_manager.notify_bot_status("Starting", f"Strategy: {strategy_name}")
        
        # Create and start trading engine
        engine = TradingEngine(strategy_name, **strategy_params)
        await engine.start()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        await notification_manager.notify_bot_status("Stopped", "Manual shutdown")
    except Exception as e:
        logger.error(f"Trading bot error: {e}")
        await notification_manager.notify_error(f"Trading bot crashed: {e}")
        raise


async def run_backtest(strategy_name: str, symbols: list, days: int = 30, **strategy_params):
    """Run a backtest"""
    try:
        logger.info(f"Starting backtest for {strategy_name}")
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        result = await backtest_engine.run_backtest(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            **strategy_params
        )
        
        # Print results
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Strategy: {result.strategy_name}")
        print(f"Period: {result.start_date.date()} to {result.end_date.date()}")
        print(f"Initial Balance: ${result.initial_balance:,.2f}")
        print(f"Final Balance: ${result.final_balance:,.2f}")
        print(f"Total Return: ${result.total_return:,.2f} ({result.total_return_pct:.2%})")
        print(f"Max Drawdown: ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2%})")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2%}")
        print(f"Profit Factor: {result.profit_factor:.2f}")
        print("="*50)
        
        return result
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise


def update_data(symbols: Optional[List[str]] = None, timeframes: Optional[List[str]] = None):
    """Update market data"""
    try:
        logger.info("Updating market data...")
        
        if not symbols:
            # Get top symbols by volume
            from src.binance_client import binance_client
            symbols = binance_client.filter_symbols_by_criteria(
                min_volume_24h=config.trading.min_volume_24h,
                max_symbols=50
            )
        
        if not timeframes:
            timeframes = ["15m", "1h", "4h", "1d"]
        
        # Update symbol info first
        data_manager.update_symbol_info()
        
        # Update market data using bulk collection
        data_manager.bulk_collect_data(symbols, timeframes)
        
        logger.info("Market data update completed")
        
    except Exception as e:
        logger.error(f"Data update failed: {e}")
        raise


async def test_notifications():
    """Test notification system"""
    try:
        logger.info("Testing notification system...")
        
        results = await notification_manager.test_notifications()
        
        print("\nNotification Test Results:")
        print("-" * 30)
        for channel, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{channel.capitalize()}: {status}")
        
        return results
        
    except Exception as e:
        logger.error(f"Notification test failed: {e}")
        raise


def main():
    """Main entry point"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Binance Trading Bot")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Trading command
    trade_parser = subparsers.add_parser("trade", help="Start trading")
    trade_parser.add_argument("--strategy", default="ma_cross", help="Trading strategy")
    trade_parser.add_argument("--fast-period", type=int, default=12, help="Fast MA period")
    trade_parser.add_argument("--slow-period", type=int, default=26, help="Slow MA period")
    
    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run backtest")
    backtest_parser.add_argument("--strategy", default="ma_cross", help="Trading strategy")
    backtest_parser.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"], help="Symbols to test")
    backtest_parser.add_argument("--days", type=int, default=30, help="Number of days to backtest")
    backtest_parser.add_argument("--fast-period", type=int, default=12, help="Fast MA period")
    backtest_parser.add_argument("--slow-period", type=int, default=26, help="Slow MA period")
    
    # API server command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # Data update command
    data_parser = subparsers.add_parser("update-data", help="Update market data")
    data_parser.add_argument("--symbols", nargs="+", help="Symbols to update")
    data_parser.add_argument("--timeframes", nargs="+", help="Timeframes to update")
    
    # Test notifications command
    subparsers.add_parser("test-notifications", help="Test notification system")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "trade":
            strategy_params = {}
            if hasattr(args, 'fast_period'):
                strategy_params['fast_period'] = args.fast_period
            if hasattr(args, 'slow_period'):
                strategy_params['slow_period'] = args.slow_period
            
            asyncio.run(run_trading_bot(args.strategy, **strategy_params))
            
        elif args.command == "backtest":
            strategy_params = {}
            if hasattr(args, 'fast_period'):
                strategy_params['fast_period'] = args.fast_period
            if hasattr(args, 'slow_period'):
                strategy_params['slow_period'] = args.slow_period
            
            asyncio.run(run_backtest(args.strategy, args.symbols, args.days, **strategy_params))
            
        elif args.command == "api":
            run_api_server(args.host, args.port)
            
        elif args.command == "update-data":
            update_data(args.symbols, args.timeframes)
            
        elif args.command == "test-notifications":
            asyncio.run(test_notifications())
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
