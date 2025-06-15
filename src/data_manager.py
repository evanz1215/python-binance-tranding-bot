"""
Data manager for handling market data collection and storage
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .config import config
from .binance_client import binance_client
from .database.models import MarketData, Symbol, get_session_factory


class DataManager:
    """Manages market data collection, storage and retrieval"""
    
    def __init__(self):
        self.session_factory = get_session_factory(config.database.url)
        self.timeframes = {
            "1m": "1m",
            "5m": "5m", 
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        
    def get_session(self) -> Session:
        """Get database session"""
        return self.session_factory()
    
    def update_symbol_info(self) -> None:
        """Update symbol information in database"""
        try:
            logger.info("Updating symbol information...")
            symbols_info = binance_client.get_symbol_info()
            
            # Ensure symbols_info is a list
            if not isinstance(symbols_info, list):
                symbols_info = [symbols_info] if symbols_info else []
            
            with self.get_session() as session:
                for symbol_data in symbols_info:
                    if symbol_data.get('status') != 'TRADING':
                        continue
                        
                    # Get or create symbol
                    symbol_name = symbol_data.get('symbol')
                    if not symbol_name:
                        continue
                        
                    symbol = session.query(Symbol).filter_by(
                        symbol=symbol_name
                    ).first()
                    
                    if not symbol:
                        symbol = Symbol(symbol=symbol_name)
                        session.add(symbol)
                    
                    # Update symbol data using setattr to avoid SQLAlchemy typing issues
                    setattr(symbol, 'base_asset', symbol_data.get('baseAsset', ''))
                    setattr(symbol, 'quote_asset', symbol_data.get('quoteAsset', ''))
                    setattr(symbol, 'status', symbol_data.get('status', ''))
                    setattr(symbol, 'is_active', symbol_data.get('status') == 'TRADING')
                    
                    # Update filters
                    filters = symbol_data.get('filters', [])
                    for filter_data in filters:
                        filter_type = filter_data.get('filterType')
                        if filter_type == 'LOT_SIZE':
                            setattr(symbol, 'min_qty', float(filter_data.get('minQty', 0)))
                            setattr(symbol, 'max_qty', float(filter_data.get('maxQty', 0)))
                            setattr(symbol, 'step_size', float(filter_data.get('stepSize', 0)))
                        elif filter_type == 'PRICE_FILTER':
                            setattr(symbol, 'min_price', float(filter_data.get('minPrice', 0)))
                            setattr(symbol, 'max_price', float(filter_data.get('maxPrice', 0)))
                            setattr(symbol, 'tick_size', float(filter_data.get('tickSize', 0)))
                        elif filter_type == 'MIN_NOTIONAL':
                            setattr(symbol, 'min_notional', float(filter_data.get('minNotional', 0)))
                    
                    setattr(symbol, 'updated_at', datetime.utcnow())
                
                session.commit()
                logger.info(f"Updated {len(symbols_info)} symbols")
                
        except Exception as e:
            logger.error(f"Failed to update symbol info: {e}")
            raise
    
    def get_active_symbols(self, quote_asset: str = "USDT") -> List[str]:
        """Get list of active trading symbols"""
        try:
            with self.get_session() as session:
                symbols = session.query(Symbol).filter(
                    Symbol.is_active == True,
                    Symbol.quote_asset == quote_asset,
                    Symbol.status == 'TRADING'
                ).all()
                
                return [getattr(s, 'symbol', '') for s in symbols]
        except Exception as e:
            logger.error(f"Failed to get active symbols: {e}")
            return []
    
    def collect_market_data(self, symbol: str, timeframe: str, 
                          limit: int = 500, start_time: Optional[datetime] = None) -> bool:
        """Collect and store market data for a symbol"""
        try:
            logger.debug(f"Collecting {timeframe} data for {symbol}")
            
            # Get klines from Binance
            klines = binance_client.get_klines(
                symbol=symbol,
                interval=timeframe,
                limit=limit,
                start_time=start_time
            )
            
            if not klines:
                logger.warning(f"No data received for {symbol} {timeframe}")
                return False
            
            with self.get_session() as session:
                for kline in klines:
                    # Parse kline data
                    timestamp = datetime.fromtimestamp(int(kline[0]) / 1000)
                    open_price = float(kline[1])
                    high_price = float(kline[2])
                    low_price = float(kline[3])
                    close_price = float(kline[4])
                    volume = float(kline[5])
                    quote_volume = float(kline[7])
                    trades_count = int(kline[8])
                    
                    # Check if data already exists
                    existing = session.query(MarketData).filter_by(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=timestamp
                    ).first()
                    
                    if existing:                        # Update existing data using setattr
                        setattr(existing, 'open', open_price)
                        setattr(existing, 'high', high_price)
                        setattr(existing, 'low', low_price)
                        setattr(existing, 'close', close_price)
                        setattr(existing, 'volume', volume)
                        setattr(existing, 'quote_volume', quote_volume)
                        setattr(existing, 'trades_count', trades_count)
                        setattr(existing, 'updated_at', datetime.utcnow())
                    else:
                        # Create new data
                        market_data = MarketData(
                            symbol=symbol,
                            timeframe=timeframe,
                            timestamp=timestamp,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume,
                            quote_volume=quote_volume,
                            trades_count=trades_count
                        )
                        session.add(market_data)
                
                session.commit()
                logger.debug(f"Stored {len(klines)} records for {symbol} {timeframe}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to collect market data for {symbol}: {e}")
            return False
    
    def get_market_data(self, symbol: str, timeframe: str,
                       start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                       limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve market data from database"""
        try:
            with self.get_session() as session:
                query = session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe
                ).order_by(MarketData.timestamp)
                
                if start_time:
                    query = query.filter(MarketData.timestamp >= start_time)
                if end_time:
                    query = query.filter(MarketData.timestamp <= end_time)
                if limit:
                    query = query.limit(limit)
                
                records = query.all()
                
                if not records:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = []
                for record in records:
                    data.append({
                        'timestamp': record.timestamp,
                        'open': record.open,
                        'high': record.high,
                        'low': record.low,
                        'close': record.close,
                        'volume': record.volume,
                        'quote_volume': record.quote_volume,
                        'trades_count': record.trades_count
                    })
                
                df = pd.DataFrame(data)
                df.set_index('timestamp', inplace=True)
                return df
                
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """Get the latest timestamp for a symbol/timeframe"""
        try:
            with self.get_session() as session:
                latest = session.query(MarketData).filter_by(
                    symbol=symbol,
                    timeframe=timeframe
                ).order_by(MarketData.timestamp.desc()).first()
                
                return latest.timestamp if latest else None
        except Exception as e:
            logger.error(f"Failed to get latest timestamp: {e}")
            return None
    
    def bulk_collect_data(self, symbols: List[str], 
                         timeframes: Optional[List[str]] = None) -> None:
        """Bulk collect data for multiple symbols and timeframes"""
        try:
            if timeframes is None:
                timeframes = ["1h", "4h", "1d"]
            
            total_tasks = len(symbols) * len(timeframes)
            completed = 0
            
            for symbol in symbols:
                for timeframe in timeframes:
                    try:
                        success = self.collect_market_data(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=100  # Smaller batches for bulk collection
                        )
                        completed += 1
                        
                        if completed % 10 == 0:
                            logger.info(f"Progress: {completed}/{total_tasks} tasks completed")
                              # Rate limiting
                        import time
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Failed to collect {symbol} {timeframe}: {e}")
                        continue
            
            logger.info(f"Bulk collection completed: {completed}/{total_tasks}")
            
        except Exception as e:
            logger.error(f"Bulk data collection failed: {e}")
            raise
    
    def update_missing_data(self) -> None:
        """Update missing data for active symbols"""
        try:
            active_symbols = self.get_active_symbols()
            
            for symbol in active_symbols[:10]:  # Limit to prevent overload
                for timeframe in ["1h", "4h"]:
                    try:
                        latest_time = self.get_latest_timestamp(symbol, timeframe)
                        
                        # If no data or data is older than 5 minutes, collect new data
                        if not latest_time or isinstance(latest_time, datetime):
                            if not latest_time or latest_time < datetime.utcnow() - timedelta(minutes=5):
                                self.collect_market_data(symbol, timeframe, start_time=latest_time)
                        
                    except Exception as e:
                        logger.error(f"Failed to update missing data for {symbol}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Failed to update missing data: {e}")
            raise
    
    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old market data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.get_session() as session:
                deleted = session.query(MarketData).filter(
                    MarketData.timestamp < cutoff_date
                ).delete()
                
                session.commit()
                logger.info(f"Cleaned up {deleted} old records")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise


# Global data manager instance
data_manager = DataManager()
