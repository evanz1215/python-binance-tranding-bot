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
        self.timeframes = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        
    def get_session(self) -> Session:
        """Get database session"""
        return self.session_factory()
        
    def update_symbol_info(self) -> None:
        """Update symbol information in database"""
        try:
            logger.info("Updating symbol information...")
            symbols_info = binance_client.get_all_symbols_info()

            # Ensure symbols_info is a list
            if not isinstance(symbols_info, list):
                symbols_info = [symbols_info] if symbols_info else []

            with self.get_session() as session:
                for symbol_data in symbols_info:
                    if symbol_data.get("status") != "TRADING":
                        continue

                    # Get or create symbol
                    symbol_name = symbol_data.get("symbol")
                    if not symbol_name:
                        continue

                    symbol = session.query(Symbol).filter_by(symbol=symbol_name).first()

                    if symbol:
                        # Update existing symbol
                        symbol.status = symbol_data.get("status", "UNKNOWN")
                        symbol.updated_at = datetime.utcnow()
                    else:
                        # Create new symbol
                        filters = {f["filterType"]: f for f in symbol_data.get("filters", [])}

                        symbol = Symbol(
                            symbol=symbol_name,
                            base_asset=symbol_data.get("baseAsset", ""),
                            quote_asset=symbol_data.get("quoteAsset", ""),
                            status=symbol_data.get("status", "UNKNOWN"),
                            is_active=symbol_data.get("status") == "TRADING",
                            min_qty=float(filters.get("LOT_SIZE", {}).get("minQty", 0)),
                            max_qty=float(filters.get("LOT_SIZE", {}).get("maxQty", 0)),
                            step_size=float(filters.get("LOT_SIZE", {}).get("stepSize", 0)),
                            min_price=float(filters.get("PRICE_FILTER", {}).get("minPrice", 0)),
                            max_price=float(filters.get("PRICE_FILTER", {}).get("maxPrice", 0)),
                            tick_size=float(filters.get("PRICE_FILTER", {}).get("tickSize", 0)),
                            min_notional=float(
                                filters.get("MIN_NOTIONAL", {}).get("minNotional", 0)
                            ),
                        )
                        session.add(symbol)

                session.commit()
                logger.info(f"Updated {len(symbols_info)} symbols")

        except Exception as e:
            logger.error(f"Failed to update symbol info: {e}")
            raise

    def collect_market_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1000,
        start_time: Optional[datetime] = None,
    ) -> bool:
        """Collect market data for a specific symbol and timeframe"""
        try:
            # Get historical klines from Binance
            start_timestamp = int(start_time.timestamp() * 1000) if start_time else None
            klines = binance_client.get_klines(
                symbol=symbol, interval=timeframe, limit=limit, start_time=start_timestamp
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
                    existing = (
                        session.query(MarketData)
                        .filter_by(symbol=symbol, timeframe=timeframe, open_time=timestamp)
                        .first()
                    )

                    if existing:  # Update existing data using setattr
                        setattr(existing, "open_price", open_price)
                        setattr(existing, "high_price", high_price)
                        setattr(existing, "low_price", low_price)
                        setattr(existing, "close_price", close_price)
                        setattr(existing, "volume", volume)
                        setattr(existing, "quote_volume", quote_volume)
                        setattr(existing, "trades_count", trades_count)
                        setattr(existing, "close_time", datetime.fromtimestamp(int(kline[6]) / 1000))
                    else:
                        # Create new data
                        market_data = MarketData(
                            symbol=symbol,
                            timeframe=timeframe,
                            open_time=timestamp,
                            close_time=datetime.fromtimestamp(int(kline[6]) / 1000),
                            open_price=open_price,
                            high_price=high_price,
                            low_price=low_price,
                            close_price=close_price,
                            volume=volume,
                            quote_volume=quote_volume,
                            trades_count=trades_count,
                        )
                        session.add(market_data)

                session.commit()
                logger.debug(f"Stored {len(klines)} records for {symbol} {timeframe}")
                return True

        except Exception as e:
            logger.error(f"Failed to collect market data for {symbol}: {e}")
            return False

    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Retrieve market data from database"""
        try:
            with self.get_session() as session:
                query = (
                    session.query(MarketData)
                    .filter(MarketData.symbol == symbol, MarketData.timeframe == timeframe)
                    .order_by(MarketData.open_time)
                )

                if start_time:
                    query = query.filter(MarketData.open_time >= start_time)
                if end_time:
                    query = query.filter(MarketData.open_time <= end_time)
                if limit:
                    query = query.limit(limit)

                records = query.all()

                if not records:
                    return pd.DataFrame()

                # Convert to DataFrame
                data = []
                for record in records:
                    data.append(
                        {
                            "timestamp": record.open_time,
                            "open": record.open_price,
                            "high": record.high_price,
                            "low": record.low_price,
                            "close": record.close_price,
                            "volume": record.volume,
                            "quote_volume": record.quote_volume,
                            "trades_count": record.trades_count,
                        }
                    )

                df = pd.DataFrame(data)
                df.set_index("timestamp", inplace=True)
                return df

        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return pd.DataFrame()

    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """Get the latest timestamp for a symbol/timeframe"""
        try:
            with self.get_session() as session:
                latest = (
                    session.query(MarketData)
                    .filter_by(symbol=symbol, timeframe=timeframe)
                    .order_by(MarketData.open_time.desc())
                    .first()
                )

                return latest.open_time if latest else None
        except Exception as e:
            logger.error(f"Failed to get latest timestamp: {e}")
            return None

    def bulk_collect_data(self, symbols: List[str], timeframes: Optional[List[str]] = None) -> None:
        """Bulk collect data for multiple symbols and timeframes"""
        try:
            if timeframes is None:
                timeframes = ["1h", "4h", "1d"]

            total_tasks = len(symbols) * len(timeframes)
            completed = 0

            for symbol in symbols:
                for timeframe in timeframes:
                    try:
                        # Check if we need to update data
                        latest_time = self.get_latest_timestamp(symbol, timeframe)
                        
                        # If we have recent data (within last hour), skip this symbol/timeframe
                        if latest_time and datetime.utcnow() - latest_time < timedelta(hours=1):
                            logger.debug(f"Skipping {symbol} {timeframe} - data is recent")
                            completed += 1
                            continue

                        # Collect fresh data
                        success = self.collect_market_data(
                            symbol=symbol,
                            timeframe=timeframe,
                            limit=1000,
                            start_time=latest_time,
                        )

                        if success:
                            logger.debug(f"Successfully collected data for {symbol} {timeframe}")
                        else:
                            logger.warning(f"Failed to collect data for {symbol} {timeframe}")

                    except Exception as e:
                        logger.error(f"Error collecting data for {symbol} {timeframe}: {e}")

                    completed += 1
                    if completed % 10 == 0:
                        logger.info(f"Progress: {completed}/{total_tasks} tasks completed")

            logger.info(f"Bulk data collection completed: {completed}/{total_tasks}")

        except Exception as e:
            logger.error(f"Bulk data collection failed: {e}")
            raise

    def cleanup_old_data(self, days: int = 30) -> None:
        """Clean up old market data older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            with self.get_session() as session:
                deleted = (
                    session.query(MarketData).filter(MarketData.open_time < cutoff_date).delete()
                )

                session.commit()
                logger.info(f"Cleaned up {deleted} old records")

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise

    def ensure_data_availability(self, symbol: str, timeframe: str, required_periods: int) -> bool:
        """確保指定交易對和時間框架有足夠的歷史數據"""
        try:
            # 檢查現有數據
            latest_timestamp = self.get_latest_timestamp(symbol, timeframe)
            if not latest_timestamp:
                # 沒有數據，需要獲取歷史數據
                logger.info(f"No existing data for {symbol} {timeframe}, fetching historical data...")
                return self._fetch_historical_data(symbol, timeframe, required_periods * 2)
            
            # 檢查數據是否足夠新和足夠多
            with self.get_session() as session:
                count = session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe
                ).count()
                
                if count < required_periods:
                    logger.info(f"Insufficient data for {symbol} {timeframe} ({count}/{required_periods}), fetching more...")
                    return self._fetch_historical_data(symbol, timeframe, required_periods * 2)
                
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring data availability for {symbol} {timeframe}: {e}")
            return False
    
    def _fetch_historical_data(self, symbol: str, timeframe: str, limit: int = 500) -> bool:
        """獲取歷史數據"""
        try:
            klines = binance_client.get_klines(symbol, timeframe, limit=limit)
            if not klines:
                return False
                
            # 保存數據到資料庫
            with self.get_session() as session:
                for kline in klines:
                    existing = session.query(MarketData).filter(
                        MarketData.symbol == symbol,
                        MarketData.timeframe == timeframe,
                        MarketData.open_time == datetime.fromtimestamp(kline[0] / 1000)
                    ).first()
                    
                    if not existing:
                        market_data = MarketData(
                            symbol=symbol,
                            timeframe=timeframe,
                            open_time=datetime.fromtimestamp(kline[0] / 1000),
                            close_time=datetime.fromtimestamp(kline[6] / 1000),
                            open_price=float(kline[1]),
                            high_price=float(kline[2]),
                            low_price=float(kline[3]),
                            close_price=float(kline[4]),
                            volume=float(kline[5]),
                            quote_volume=float(kline[7]),
                            trades_count=int(kline[8]),
                        )
                        session.add(market_data)
                
                session.commit()
                logger.info(f"Stored {len(klines)} historical records for {symbol} {timeframe}")
                return True
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol} {timeframe}: {e}")
            return False

    async def update_all_market_data(self, symbols: List[str], timeframes: List[str]) -> None:
        """批量更新所有監控交易對的市場數據"""
        try:
            logger.info(f"Updating market data for {len(symbols)} symbols, {len(timeframes)} timeframes...")
            
            for symbol in symbols:
                for timeframe in timeframes:
                    try:
                        # 獲取最新的 K 線數據
                        latest_klines = binance_client.get_klines(symbol, timeframe, limit=2)
                        if latest_klines:
                            # 只保存最新的數據
                            await self._store_latest_data(symbol, timeframe, latest_klines[-1])
                            
                        # 避免 API 速率限制
                        await asyncio.sleep(0.05)
                        
                    except Exception as e:
                        logger.warning(f"Failed to update data for {symbol} {timeframe}: {e}")
                        continue
                        
            logger.info("Market data update completed")
            
        except Exception as e:
            logger.error(f"Error in update_all_market_data: {e}")
    
    async def _store_latest_data(self, symbol: str, timeframe: str, kline: List) -> None:
        """存儲最新的 K 線數據"""
        try:
            with self.get_session() as session:
                open_time = datetime.fromtimestamp(kline[0] / 1000)
                
                # 檢查是否已存在
                existing = session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                    MarketData.open_time == open_time
                ).first()
                
                if existing:
                    # 更新現有數據 (使用 session.merge 或直接更新)
                    session.query(MarketData).filter(
                        MarketData.symbol == symbol,
                        MarketData.timeframe == timeframe,
                        MarketData.open_time == open_time
                    ).update({
                        MarketData.close_time: datetime.fromtimestamp(kline[6] / 1000),
                        MarketData.open_price: float(kline[1]),
                        MarketData.high_price: float(kline[2]),
                        MarketData.low_price: float(kline[3]),
                        MarketData.close_price: float(kline[4]),
                        MarketData.volume: float(kline[5]),
                        MarketData.quote_volume: float(kline[7]),
                        MarketData.trades_count: int(kline[8])
                    })
                else:
                    # 創建新記錄
                    market_data = MarketData(
                        symbol=symbol,
                        timeframe=timeframe,
                        open_time=open_time,
                        close_time=datetime.fromtimestamp(kline[6] / 1000),
                        open_price=float(kline[1]),
                        high_price=float(kline[2]),
                        low_price=float(kline[3]),
                        close_price=float(kline[4]),
                        volume=float(kline[5]),
                        quote_volume=float(kline[7]),
                        trades_count=int(kline[8]),
                    )
                    session.add(market_data)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error storing latest data for {symbol} {timeframe}: {e}")


# Global data manager instance
data_manager = DataManager()
