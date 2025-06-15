"""
Main FastAPI application for the trading bot
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

try:
    import uvicorn
except ImportError:
    uvicorn = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..config import config
from ..trading_engine import TradingEngine
from ..backtest_engine import backtest_engine
from ..risk_manager import risk_manager
from ..data_manager_fixed import data_manager
from ..binance_client import binance_client
from .. import shared_state

from .models import StrategyConfig, BacktestRequest, TradingStatus
from .routes.trading import router as trading_router
from .routes.orders import router as orders_router
from .routes.positions import router as positions_router
from .routes.market import router as market_router
from .routes.pages import router as pages_router, get_dashboard_html

# Global trading engine instance
# trading_engine = None

# Create FastAPI app
app = FastAPI(
    title="Binance Trading Bot API",
    description="API for managing the Binance trading bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trading_router, prefix="/api/trading", tags=["trading"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(positions_router, prefix="/api/positions", tags=["positions"])
app.include_router(market_router, prefix="/api", tags=["market"])
app.include_router(pages_router, tags=["pages"])

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    return get_dashboard_html()

# Status endpoint
@app.get("/api/status", response_model=TradingStatus)
async def get_status():
    """Get current trading status"""
    
    try:
        trading_engine = shared_state.get_trading_engine()
        
        if trading_engine and trading_engine.is_running:
            # Get real data from trading engine
            positions = binance_client.get_futures_positions()
            active_positions = len([p for p in positions if float(p.get('positionAmt', 0)) != 0]) if positions else 0
            
            balance = binance_client.get_futures_account()
            total_balance = float(balance.get('totalWalletBalance', 0.0)) if balance else 0.0
            
            # Calculate daily PnL (simplified)
            daily_pnl = trading_engine.session_stats.get('daily_pnl', 0.0) if hasattr(trading_engine, 'session_stats') else 0.0
            
            return TradingStatus(
                is_running=True,
                session_id=getattr(trading_engine, 'session_id', None),
                strategy=getattr(trading_engine, 'strategy_name', "Unknown"),
                monitored_symbols=len(getattr(trading_engine, 'monitored_symbols', [])),
                active_positions=active_positions,
                risk_level="LOW",  # Simplified risk level
                total_balance=total_balance,
                daily_pnl=daily_pnl,
                last_update=datetime.utcnow()
            )
        else:
            return TradingStatus(
                is_running=False,
                session_id=None,
                strategy="None",
                monitored_symbols=0,
                active_positions=0,
                risk_level="LOW",
                total_balance=0.0,
                daily_pnl=0.0,
                last_update=datetime.utcnow()
            )
    except Exception as e:
        logger.error("Error getting status: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


def run_api_server(host="0.0.0.0", port=8000):
    """啟動 FastAPI 伺服器"""
    if uvicorn is None:
        raise ImportError("uvicorn is required to run the API server")
    uvicorn.run("src.api:app", host=host, port=port, reload=True)
