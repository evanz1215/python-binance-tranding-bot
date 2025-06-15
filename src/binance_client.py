"""
Binance API client wrapper
"""
import time
from typing import List, Dict, Any, Union, Optional
from datetime import datetime

try:
    from binance.client import Client
    from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT
    from binance.exceptions import BinanceAPIException, BinanceOrderException  # type: ignore
    BINANCE_AVAILABLE = True
except ImportError:
    # Fallback if binance module is not available
    Client = None
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    BINANCE_AVAILABLE = False
    
    class BinanceAPIException(Exception):
        pass
    
    class BinanceOrderException(Exception):
        pass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .config import config


class BinanceClient:
    """Enhanced Binance client with error handling and rate limiting"""
    
    def __init__(self):
        if Client is None:
            raise ImportError("python-binance package is required. Install with: pip install python-binance")
            
        self.client = Client(
            config.binance.api_key,
            config.binance.secret_key,
            testnet=config.binance.testnet
        )
        self.last_request_time = 0
        self.request_interval = 0.1  # Minimum interval between requests
        
    def _rate_limit(self):
        """Simple rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            time.sleep(self.request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            self._rate_limit()
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_balance(self, asset: Optional[str] = None) -> Union[Dict[str, float], Dict[str, Dict[str, float]]]:
        """Get account balance for specific asset or all assets"""
        try:
            account = self.get_account_info()
            balances = {}
            
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:  # Only include non-zero balances
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            if asset:
                return balances.get(asset, {'free': 0.0, 'locked': 0.0, 'total': 0.0})
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise
    
    def get_symbol_info(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get symbol information"""
        try:
            self._rate_limit()
            exchange_info = self.client.get_exchange_info()
            
            if symbol:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        return s
                raise ValueError(f"Symbol {symbol} not found")
            
            return exchange_info['symbols']
        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            raise
    
    def get_active_symbols(self, quote_assets: Optional[List[str]] = None) -> List[str]:
        """Get list of active trading symbols"""
        try:
            symbols_info = self.get_symbol_info()
            active_symbols = []
            
            if quote_assets is None:
                quote_assets = ['USDT', 'BTC', 'ETH', 'BNB']
            
            # Ensure symbols_info is a list
            if isinstance(symbols_info, list):
                for symbol in symbols_info:
                    if (symbol.get('status') == 'TRADING' and 
                        symbol.get('quoteAsset') in quote_assets and
                        symbol.get('isSpotTradingAllowed')):
                        active_symbols.append(symbol.get('symbol'))
            
            return active_symbols
        except Exception as e:
            logger.error(f"Failed to get active symbols: {e}")
            raise
    
    def get_24hr_ticker(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get 24hr ticker statistics"""
        try:
            self._rate_limit()
            if symbol:
                return self.client.get_ticker(symbol=symbol)
            else:
                return self.client.get_ticker()
        except Exception as e:
            logger.error(f"Failed to get 24hr ticker: {e}")
            raise    
    def get_klines(self, symbol: str, interval: str, limit: int = 500, 
                   start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Any:
        """Get kline/candlestick data"""
        try:
            self._rate_limit()
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=int(start_time.timestamp() * 1000) if start_time else None,
                endTime=int(end_time.timestamp() * 1000) if end_time else None
            )
            return klines
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: float, price: Optional[float] = None, 
                   stop_price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """Place a new order"""
        try:
            self._rate_limit()
            
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
            }
            
            if price:
                order_params['price'] = price
            if stop_price:
                order_params['stopPrice'] = stop_price
                
            # Add any additional parameters
            order_params.update(kwargs)
            
            logger.info(f"Placing order: {order_params}")
            
            if config.binance.testnet:
                # In testnet, we can actually place the order
                return self.client.create_order(**order_params)
            else:
                # In live trading, add additional safety checks
                return self.client.create_order(**order_params)
                
        except BinanceOrderException as e:
            logger.error(f"Order failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            self._rate_limit()
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            self._rate_limit()
            result = self.client.get_open_orders(symbol=symbol)
            # Ensure we return a list
            if isinstance(result, list):
                return result
            else:
                return [result] if result else []
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        try:
            self._rate_limit()
            return self.client.get_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise
    
    def get_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get account trade list"""
        try:
            self._rate_limit()
            result = self.client.get_my_trades(symbol=symbol, limit=limit)
            # Ensure we return a list
            if isinstance(result, list):
                return result
            else:
                return [result] if result else []
        except Exception as e:
            logger.error(f"Failed to get trades: {e}")
            raise
    
    def filter_symbols_by_criteria(self, min_volume_24h: Optional[float] = None,
                                  max_symbols: Optional[int] = None) -> List[str]:
        """Filter symbols based on volume and other criteria"""
        try:
            tickers = self.get_24hr_ticker()
            filtered_symbols = []
            
            # Ensure tickers is a list
            if not isinstance(tickers, list):
                tickers = [tickers] if tickers else []
            
            for ticker in tickers:
                symbol = ticker.get('symbol', '')
                volume_24h = float(ticker.get('quoteVolume', 0))
                
                # Apply whitelist/blacklist
                if hasattr(config.trading, 'whitelist') and config.trading.whitelist and symbol not in config.trading.whitelist:
                    continue
                if hasattr(config.trading, 'blacklist') and config.trading.blacklist and symbol in config.trading.blacklist:
                    continue
                
                # Apply volume filter
                if min_volume_24h and volume_24h < min_volume_24h:
                    continue
                
                # Only include USDT pairs for simplicity
                if not symbol.endswith('USDT'):
                    continue
                
                filtered_symbols.append(symbol)
            
            # Sort by volume (descending) and limit
            filtered_symbols.sort(
                key=lambda s: float([t for t in tickers if t.get('symbol') == s][0].get('quoteVolume', 0)),
                reverse=True
            )
            
            if max_symbols:
                filtered_symbols = filtered_symbols[:max_symbols]
            
            logger.info(f"Filtered {len(filtered_symbols)} symbols from {len(tickers)} total")
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Failed to filter symbols: {e}")
            raise
    
    def calculate_quantity(self, symbol: str, usdt_amount: float, price: float) -> float:
        """Calculate quantity based on USDT amount and current price"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info or isinstance(symbol_info, list):
                raise ValueError(f"Symbol {symbol} not found")
            
            # Get lot size filter
            lot_size_filter = None
            for f in symbol_info.get('filters', []):
                if f.get('filterType') == 'LOT_SIZE':
                    lot_size_filter = f
                    break
            
            if not lot_size_filter:
                raise ValueError(f"LOT_SIZE filter not found for {symbol}")
            
            min_qty = float(lot_size_filter.get('minQty', 0))
            step_size = float(lot_size_filter.get('stepSize', 1))
            
            # Calculate quantity
            quantity = usdt_amount / price
            
            # Round to step size
            quantity = round(quantity / step_size) * step_size
            
            # Ensure minimum quantity
            if quantity < min_qty:
                raise ValueError(f"Calculated quantity {quantity} is less than minimum {min_qty}")
            
            return quantity
            
        except Exception as e:
            logger.error(f"Failed to calculate quantity: {e}")
            raise


# Global client instance
try:
    binance_client = BinanceClient()
except ImportError as e:
    logger.warning(f"BinanceClient initialization failed: {e}")
    binance_client = None
