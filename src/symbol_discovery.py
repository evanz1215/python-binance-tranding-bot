"""
Advanced Symbol Discovery and Filtering System
自動化幣種發現與篩选系統
"""
import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .config import config
from .binance_client import binance_client


@dataclass
class SymbolMetrics:
    """Symbol metrics for filtering and ranking"""
    symbol: str
    volume_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    quote_volume: float
    trade_count: int
    volatility_score: float
    momentum_score: float
    liquidity_score: float
    overall_score: float


class SymbolDiscovery:
    """Advanced symbol discovery and filtering system"""
    
    def __init__(self):
        self.last_update_time = None
        self.cached_symbols = []
        self.excluded_symbols = self._get_excluded_symbols()
        self.update_interval = int(os.getenv("UPDATE_SYMBOLS_INTERVAL", "1800"))  # 30 minutes
        
    def _get_excluded_symbols(self) -> Set[str]:
        """Get list of symbols to exclude"""
        excluded = set()
        
        # Stablecoins
        if os.getenv("EXCLUDE_STABLECOINS", "true").lower() == "true":
            stablecoins = {
                'USDTUSDT', 'USDCUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT',
                'PAXUSDT', 'USTUSDT', 'FRAXUSDT', 'LUSDUSDT'
            }
            excluded.update(stablecoins)
        
        # Add user-defined blacklist
        if hasattr(config.trading, 'blacklist') and config.trading.blacklist:
            excluded.update(config.trading.blacklist)
            
        # Known problematic or delisted coins
        problematic = {
            'LUNAUSDT', 'USTCUSDT', 'COCOSUSDT', 'VENUSDT', 'BCCUSDT'
        }
        excluded.update(problematic)
        
        return excluded
    
    async def discover_symbols(self, force_update: bool = False) -> List[str]:
        """
        Discover and filter symbols based on advanced criteria
        
        Args:
            force_update: Force update even if cache is still valid
            
        Returns:
            List of filtered symbol names
        """
        try:
            # Check if cache is still valid
            if not force_update and self._is_cache_valid():
                logger.debug("Using cached symbols")
                return self.cached_symbols
            
            logger.info("Starting advanced symbol discovery...")
            
            # Get all 24hr ticker data
            tickers = binance_client.get_24hr_ticker()
            if not isinstance(tickers, list):
                tickers = [tickers] if tickers else []
            
            # Calculate metrics for each symbol
            symbol_metrics = []
            for ticker in tickers:
                metrics = self._calculate_symbol_metrics(ticker)
                if metrics and self._passes_basic_filters(metrics):
                    symbol_metrics.append(metrics)
            
            # Apply advanced filtering
            filtered_metrics = await self._apply_advanced_filters(symbol_metrics)
            
            # Rank and select top symbols
            selected_symbols = self._rank_and_select_symbols(filtered_metrics)
            
            # Update cache
            self.cached_symbols = selected_symbols
            self.last_update_time = datetime.utcnow()
            
            logger.info(f"Symbol discovery completed: {len(selected_symbols)} symbols selected")
            return selected_symbols
            
        except Exception as e:
            logger.error(f"Error in symbol discovery: {e}")
            return self.cached_symbols if self.cached_symbols else []
    
    def _calculate_symbol_metrics(self, ticker: Dict[str, Any]) -> Optional[SymbolMetrics]:
        """Calculate comprehensive metrics for a symbol"""
        try:
            symbol = ticker.get('symbol', '')
            volume_24h = float(ticker.get('volume', 0))
            quote_volume = float(ticker.get('quoteVolume', 0))
            price_change = float(ticker.get('priceChange', 0))
            price_change_percent = float(ticker.get('priceChangePercent', 0))
            high_24h = float(ticker.get('highPrice', 0))
            low_24h = float(ticker.get('lowPrice', 0))
            last_price = float(ticker.get('lastPrice', 0))
            trade_count = int(ticker.get('count', 0))
            
            # Calculate volatility score (0-100)
            if last_price > 0:
                daily_range = high_24h - low_24h
                volatility_score = min(100, (daily_range / last_price) * 100)
            else:
                volatility_score = 0
            
            # Calculate momentum score based on price change
            momentum_score = min(100, abs(price_change_percent) * 2)
            
            # Calculate liquidity score based on volume and trade count
            liquidity_score = min(100, (quote_volume / 1000000) + (trade_count / 10000))
            
            # Calculate overall score (weighted average)
            overall_score = (
                volatility_score * 0.3 +
                momentum_score * 0.4 +
                liquidity_score * 0.3
            )
            
            return SymbolMetrics(
                symbol=symbol,
                volume_24h=volume_24h,
                price_change_24h=price_change,
                price_change_percent_24h=price_change_percent,
                quote_volume=quote_volume,
                trade_count=trade_count,
                volatility_score=volatility_score,
                momentum_score=momentum_score,
                liquidity_score=liquidity_score,
                overall_score=overall_score
            )
            
        except Exception as e:
            logger.debug(f"Error calculating metrics for ticker: {e}")
            return None
    
    def _passes_basic_filters(self, metrics: SymbolMetrics) -> bool:
        """Apply basic filtering criteria"""
        # Must be USDT pair
        if not metrics.symbol.endswith('USDT'):
            return False
        
        # Check exclusion list
        if metrics.symbol in self.excluded_symbols:
            return False
        
        # Apply whitelist if specified
        if hasattr(config.trading, 'whitelist') and config.trading.whitelist:
            return metrics.symbol in config.trading.whitelist
        
        # Minimum volume requirement
        min_volume = float(os.getenv("MIN_DAILY_VOLUME_USD", "10000000"))
        if metrics.quote_volume < min_volume:
            return False
        
        # Price change threshold
        price_change_threshold = float(os.getenv("PRICE_CHANGE_THRESHOLD", "5.0"))
        if abs(metrics.price_change_percent_24h) < price_change_threshold:
            return False
        
        # Volatility filter
        if os.getenv("VOLATILITY_FILTER", "true").lower() == "true":
            if metrics.volatility_score > 50:  # Too volatile
                return False
            if metrics.volatility_score < 5:   # Too stable
                return False
        
        return True
    
    async def _apply_advanced_filters(self, metrics_list: List[SymbolMetrics]) -> List[SymbolMetrics]:
        """Apply advanced filtering based on additional criteria"""
        filtered = []
        
        for metrics in metrics_list:
            try:
                # Skip if already in current positions
                # TODO: Add position check logic here
                
                # Check trading pair status
                symbol_info = binance_client.get_symbol_info(metrics.symbol)
                if not symbol_info or symbol_info.get('status') != 'TRADING':
                    continue
                
                # Additional technical filters can be added here
                # For example: RSI, moving averages, etc.
                
                filtered.append(metrics)
                
            except Exception as e:
                logger.debug(f"Error in advanced filtering for {metrics.symbol}: {e}")
                continue
        
        return filtered
    
    def _apply_advanced_filters_sync(self, metrics_list: List[SymbolMetrics]) -> List[SymbolMetrics]:
        """Apply advanced filtering based on additional criteria (sync version)"""
        filtered = []
        
        for metrics in metrics_list:
            try:
                # Skip if already in current positions
                # TODO: Add position check logic here
                
                # Check trading pair status
                symbol_info = binance_client.get_symbol_info(metrics.symbol)
                if not symbol_info or symbol_info.get('status') != 'TRADING':
                    continue
                
                # Additional technical filters can be added here
                # For example: RSI, moving averages, etc.
                
                filtered.append(metrics)
                
            except Exception as e:
                logger.debug(f"Error in advanced filtering for {metrics.symbol}: {e}")
                continue
        
        return filtered
    
    def _rank_and_select_symbols(self, metrics_list: List[SymbolMetrics]) -> List[str]:
        """Rank symbols by overall score and select top candidates"""
        # Sort by overall score (descending)
        sorted_metrics = sorted(metrics_list, key=lambda x: x.overall_score, reverse=True)
        
        # Get maximum number of symbols to monitor
        max_symbols = int(os.getenv("MAX_MONITORED_SYMBOLS", "30"))
        
        # Select top symbols
        selected = [m.symbol for m in sorted_metrics[:max_symbols]]
        
        # Log selection details
        if selected:
            logger.info("Top selected symbols:")
            for i, metrics in enumerate(sorted_metrics[:min(10, len(selected))]):
                logger.info(f"  {i+1}. {metrics.symbol}: Score={metrics.overall_score:.1f}, "
                           f"Volume=${metrics.quote_volume/1000000:.1f}M, "
                           f"Change={metrics.price_change_percent_24h:.2f}%")
        
        return selected
    
    def _is_cache_valid(self) -> bool:
        """Check if cached symbols are still valid"""
        if not self.last_update_time or not self.cached_symbols:
            return False
        
        time_since_update = datetime.utcnow() - self.last_update_time
        return time_since_update.total_seconds() < self.update_interval
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a specific symbol"""
        try:
            ticker = binance_client.get_24hr_ticker(symbol)
            if isinstance(ticker, list):
                ticker = ticker[0] if ticker else {}
            
            metrics = self._calculate_symbol_metrics(ticker)
            
            return {
                'symbol': symbol,
                'current_price': float(ticker.get('lastPrice', 0)),
                'volume_24h': float(ticker.get('quoteVolume', 0)),
                'price_change_24h': float(ticker.get('priceChangePercent', 0)),
                'metrics': metrics.__dict__ if metrics else None,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return {}
    
    async def update_symbols_periodically(self):
        """Background task to update symbols periodically"""
        while True:
            try:
                await self.discover_symbols(force_update=True)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in periodic symbol update: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def discover_symbols_sync(self, force_update: bool = False) -> List[str]:
        """
        Synchronous version of discover_symbols for use in sync contexts
        
        Args:
            force_update: Force update even if cache is still valid
            
        Returns:
            List of filtered symbol names
        """
        try:
            # Check if cache is still valid
            if not force_update and self._is_cache_valid():
                logger.debug("Using cached symbols")
                return self.cached_symbols
            
            logger.info("Starting advanced symbol discovery (sync)...")
            
            # Get all 24hr ticker data
            tickers = binance_client.get_24hr_ticker()
            if not isinstance(tickers, list):
                tickers = [tickers] if tickers else []
            
            # Calculate metrics for each symbol
            symbol_metrics = []
            for ticker in tickers:
                metrics = self._calculate_symbol_metrics(ticker)
                if metrics and self._passes_basic_filters(metrics):
                    symbol_metrics.append(metrics)
            
            # Apply advanced filtering (sync version)
            filtered_metrics = self._apply_advanced_filters_sync(symbol_metrics)
            
            # Rank and select top symbols
            selected_symbols = self._rank_and_select_symbols(filtered_metrics)
            
            # Update cache
            self.cached_symbols = selected_symbols
            self.last_update_time = datetime.utcnow()
            
            logger.info(f"Symbol discovery completed (sync): {len(selected_symbols)} symbols selected")
            return selected_symbols
            
        except Exception as e:
            logger.error(f"Error in symbol discovery (sync): {e}")
            return self.cached_symbols if self.cached_symbols else []


# Global instance
symbol_discovery = SymbolDiscovery()


# Utility functions for backward compatibility
def get_monitored_symbols() -> List[str]:
    """Get list of symbols to monitor (synchronous version)"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(symbol_discovery.discover_symbols())
    except RuntimeError:
        # If no event loop is running, create a new one
        return asyncio.run(symbol_discovery.discover_symbols())


def is_auto_discovery_enabled() -> bool:
    """Check if automatic symbol discovery is enabled"""
    return os.getenv("AUTO_SYMBOL_DISCOVERY", "true").lower() == "true"
