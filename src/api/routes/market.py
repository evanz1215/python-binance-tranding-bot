"""
Market data and symbols related API routes
"""
from fastapi import APIRouter, HTTPException

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ...config import config
from ...binance_client import binance_client
from ...data_manager_fixed import data_manager

router = APIRouter()

@router.get("/symbols")
async def get_symbols():
    """Get list of available symbols"""
    try:
        symbols = binance_client.filter_symbols_by_criteria(
            min_volume_24h=config.trading.min_volume_24h
        )
        return {"symbols": symbols}
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def get_strategies():
    """Get list of available strategies"""
    try:
        from ...strategies import STRATEGIES
        
        strategies = []
        for name, strategy_class in STRATEGIES.items():
            strategies.append({
                "name": name,
                "description": strategy_class.__doc__ or f"{name} strategy"
            })
        
        return {"strategies": strategies}
    except Exception as e:
        logger.error("Error getting strategies: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/market-data/{symbol}/{timeframe}")
async def get_market_data(symbol: str, timeframe: str, limit: int = 100):
    """Get market data for a symbol"""
    try:
        df = data_manager.get_market_data(symbol, timeframe, limit=limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Convert to list of dicts for JSON response
        data = []
        for timestamp, row in df.iterrows():
            data.append({
                "timestamp": str(timestamp),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
            })
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance():
    """Get account balance"""
    try:
        balance = binance_client.get_futures_account()
        return balance
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account/balances")
async def get_account_balances():
    """Get detailed account balances"""
    try:
        account = binance_client.get_futures_account()
        return account.get('assets', []) if account else []
    except Exception as e:
        logger.error(f"Error getting account balances: {e}")
        return []
