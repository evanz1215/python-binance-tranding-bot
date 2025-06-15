"""
Trading-related API routes
"""
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ...trading_engine import TradingEngine
from ...backtest_engine import backtest_engine
from ...risk_manager import risk_manager
from ... import shared_state
from ..models import StrategyConfig, BacktestRequest

router = APIRouter()

@router.post("/start")
async def start_trading(background_tasks: BackgroundTasks, strategy: Optional[StrategyConfig] = None):
    """Start the trading bot"""
    try:
        trading_engine = shared_state.get_trading_engine()
        
        if trading_engine and hasattr(trading_engine, 'is_running') and trading_engine.is_running:
            return {"message": "Trading bot is already running"}
        
        logger.info("Creating new trading engine...")
        
        # Create new trading engine
        if strategy:
            new_engine = TradingEngine(strategy.name, **strategy.parameters)
        else:
            new_engine = TradingEngine("ma_cross")  # Default strategy
        
        shared_state.set_trading_engine(new_engine)
        logger.info(f"Trading engine created, starting in background...")
        
        # Start in background and wait a bit to check if it started successfully
        async def start_and_check():
            try:
                await new_engine.start()
                logger.info(f"Trading engine started successfully, is_running: {new_engine.is_running}")
            except Exception as e:
                logger.error(f"Trading engine failed to start: {e}")
                new_engine.is_running = False
                raise
        
        background_tasks.add_task(start_and_check)
        
        # Give it a moment to start
        await asyncio.sleep(0.5)
        
        return {
            "message": "Trading bot started successfully", 
            "status": "starting",
            "engine_status": getattr(new_engine, 'is_running', False)
        }
        
    except Exception as e:
        logger.error("Error starting trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stop")
async def stop_trading():
    """Stop the trading bot"""
    try:
        trading_engine = shared_state.get_trading_engine()
        
        if not trading_engine or not trading_engine.is_running:
            return {"message": "Trading bot is not running"}
        
        await trading_engine.stop()
        return {"message": "Trading bot stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance():
    """Get account balance"""
    try:
        from ...binance_client import binance_client
        balance = binance_client.get_futures_account()
        return balance
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions():
    """Get current positions"""
    try:
        from ...binance_client import binance_client
        positions = binance_client.get_futures_positions()
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/report")
async def get_risk_report():
    """Get risk analysis report"""
    try:
        report = risk_manager.generate_risk_report()
        return report
    except Exception as e:
        logger.error(f"Error generating risk report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """Run backtest for a strategy"""
    try:
        logger.info(f"Starting backtest: {request.strategy.name}")
        
        result = await backtest_engine.run_backtest(
            strategy_name=request.strategy.name,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            initial_balance=request.initial_balance,
            **request.strategy.parameters
        )
        
        logger.info(f"Backtest completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_trading_history(
    symbol: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 100
):
    """Get trading history with filters"""
    try:
        # 這裡應該從資料庫獲取真實的交易歷史
        # 暫時返回示例數據
        sample_trades = [
            {
                "entry_time": "2025-06-15T10:30:00Z",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "entry_price": 42500.00,
                "exit_price": 43100.00,
                "quantity": 0.001,
                "pnl": 0.60,
                "pnl_percent": 1.41,
                "duration": "2h 15m",
                "strategy": "MA Cross"
            },
            {
                "entry_time": "2025-06-15T08:15:00Z",
                "symbol": "ETHUSDT",
                "side": "BUY",
                "entry_price": 2450.00,
                "exit_price": 2420.00,
                "quantity": 0.01,
                "pnl": -0.30,
                "pnl_percent": -1.22,
                "duration": "1h 45m",
                "strategy": "MA Cross"
            }
        ]
        
        # 應用過濾器
        filtered_trades = sample_trades
        if symbol:
            filtered_trades = [t for t in filtered_trades if t["symbol"] == symbol]
        if result == "profit":
            filtered_trades = [t for t in filtered_trades if t["pnl"] > 0]
        elif result == "loss":
            filtered_trades = [t for t in filtered_trades if t["pnl"] < 0]
            
        return filtered_trades[:limit]
    except Exception as e:
        logger.error(f"Error getting trading history: {e}")
        return []


@router.get("/stats")
async def get_trading_stats():
    """Get trading statistics"""
    try:
        # 這裡應該從資料庫計算真實的統計數據
        # 暫時返回示例數據
        stats = {
            "total_trades": 24,
            "winning_trades": 15,
            "losing_trades": 9,
            "win_rate": 62.5,
            "total_pnl": 125.50,
            "avg_win": 12.30,
            "avg_loss": -8.75,
            "profit_factor": 1.85,
            "max_drawdown": -45.20,
            "sharpe_ratio": 1.42,
            "daily_pnl": 8.75,
            "weekly_pnl": 45.20,
            "monthly_pnl": 125.50
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting trading stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
