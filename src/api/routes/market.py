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


@router.get("/monitored-symbols")
async def get_monitored_symbols():
    """Get list of currently monitored symbols"""
    try:
        from ... import shared_state
        
        trading_engine = shared_state.get_trading_engine()
        
        if trading_engine and hasattr(trading_engine, 'monitored_symbols'):
            monitored_symbols = getattr(trading_engine, 'monitored_symbols', [])
              # Get additional info for each symbol
            symbols_info = []
            for symbol in monitored_symbols:
                try:
                    # Get 24hr ticker data for each symbol
                    ticker = binance_client.get_24hr_ticker(symbol)
                    if ticker:
                        # Handle case where ticker might be a list
                        if isinstance(ticker, list):
                            ticker_data = ticker[0] if ticker else {}
                        else:
                            ticker_data = ticker
                            
                        symbols_info.append({
                            "symbol": symbol,
                            "price": float(ticker_data.get('lastPrice', 0)),
                            "change_24h": float(ticker_data.get('priceChangePercent', 0)),
                            "volume_24h": float(ticker_data.get('quoteVolume', 0)),
                            "high_24h": float(ticker_data.get('highPrice', 0)),
                            "low_24h": float(ticker_data.get('lowPrice', 0))
                        })
                    else:
                        symbols_info.append({
                            "symbol": symbol,
                            "price": 0,
                            "change_24h": 0,
                            "volume_24h": 0,
                            "high_24h": 0,
                            "low_24h": 0
                        })
                except Exception as symbol_error:
                    logger.warning(f"Error getting data for {symbol}: {symbol_error}")
                    symbols_info.append({
                        "symbol": symbol,
                        "price": 0,
                        "change_24h": 0,
                        "volume_24h": 0,
                        "high_24h": 0,
                        "low_24h": 0
                    })
            
            return {
                "monitored_symbols": symbols_info,
                "total_count": len(monitored_symbols),
                "is_auto_discovery_enabled": trading_engine.is_running,
                "last_update": getattr(trading_engine, 'last_symbol_update', None)
            }
        else:
            return {
                "monitored_symbols": [],
                "total_count": 0,
                "is_auto_discovery_enabled": False,
                "last_update": None
            }
            
    except Exception as e:
        logger.error(f"Error getting monitored symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))
