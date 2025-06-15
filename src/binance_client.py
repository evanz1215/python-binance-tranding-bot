"""
Binance API client wrapper with paper trading support
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
from . import shared_state

# Demo 模式和紙上交易支援
if config.binance.demo_mode:
    from .demo_client import demo_client
elif config.binance.paper_trading:
    from .paper_trading_client import PaperTradingClient


class BinanceClient:
    """Enhanced Binance client with error handling and rate limiting"""
    
    def __init__(self, trading_type: str = "futures"):
        self.trading_type = trading_type.lower()
        
        # 檢查交易模式
        if config.binance.demo_mode:
            logger.info("🎮 Demo 模式已啟動 - 使用完全模擬的交易客戶端")
            self.client = demo_client
            self.time_offset = 0
            self.last_request_time = 0
            self.request_interval = 0.1
            return
        elif config.binance.paper_trading:
            logger.info("📋 紙上交易模式已啟動 - 使用真實數據但虛擬資金")
            # 取得或創建 paper trading client 實例
            paper_client = shared_state.get_paper_trading_client()
            if not paper_client:
                # 創建新的 paper trading client 並註冊到 shared_state
                paper_client = PaperTradingClient()
                shared_state.set_paper_trading_client(paper_client)
                logger.info("創建新的 paper trading client 實例")
            else:
                logger.info("使用現有的 paper trading client 實例")
                
            self.client = paper_client
            self.time_offset = paper_client.time_offset
            self.last_request_time = 0
            self.request_interval = 0.1
            return
        
        # 正常模式初始化
        if Client is None:
            raise ImportError("python-binance package is required. Install with: pip install python-binance")
        
        # 獲取對應的 API 憑證
        api_key, secret_key = config.binance.get_api_credentials(self.trading_type)
        
        if not api_key or not secret_key:
            raise ValueError(f"Missing API credentials for {self.trading_type} trading")
            
        self.client = Client(
            api_key,
            secret_key,
            testnet=config.binance.testnet
        )
        
        # 啟用自動時間同步以避免時間戳錯誤
        self.time_offset = config.binance.time_offset  # 從配置讀取時間偏移
        try:
            # 獲取伺服器時間並計算時間偏移
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000) + self.time_offset
            calculated_offset = server_time['serverTime'] - local_time
            logger.info(f"Calculated server time offset: {calculated_offset}ms")
            logger.info(f"Using configured time offset: {self.time_offset}ms")
                
        except Exception as e:
            logger.warning(f"Failed to sync server time: {e}")
            
        self.last_request_time = 0
        self.request_interval = 0.1  # Minimum interval between requests        
        logger.info(f"Initialized Binance client for {self.trading_type} trading (testnet: {config.binance.testnet})")

    def get_adjusted_timestamp(self) -> int:
        """Get adjusted timestamp for API calls"""
        return int(time.time() * 1000) + self.time_offset

    def _rate_limit(self):
        """Implement rate limiting to avoid API limits"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            self._rate_limit()
            return self.client.get_account()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def get_balance(self, asset: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get account balance for specific asset or all assets"""
        try:
            account_info = self.get_account_info()
            balances = account_info.get('balances', [])
            
            if asset:
                # Return specific asset balance
                for balance in balances:
                    if balance.get('asset') == asset:
                        return balance
                return {'asset': asset, 'free': '0.0', 'locked': '0.0'}
            else:
                # Return all balances
                return balances
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    def get_klines(self, symbol: str, interval: str, limit: int = 500, 
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[List[str]]:
        """Get kline/candlestick data"""
        try:
            self._rate_limit()
            kwargs = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            if start_time:
                kwargs['startTime'] = start_time
            if end_time:
                kwargs['endTime'] = end_time
                
            return self.client.get_klines(**kwargs)
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise

    def get_ticker_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get current price for symbol(s)"""
        try:
            self._rate_limit()
            if symbol:
                return self.client.get_symbol_ticker(symbol=symbol)
            else:
                return self.client.get_all_tickers()
        except Exception as e:
            logger.error(f"Failed to get ticker price: {e}")
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

    def place_order(self, symbol: str, side: str, order_type: str, 
                   quantity: Optional[float] = None, price: Optional[float] = None,
                   time_in_force: str = 'GTC', **kwargs) -> Dict[str, Any]:
        """Place an order with enhanced error handling"""
        try:
            self._rate_limit()
            
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'timeInForce': time_in_force,
                'timestamp': self.get_adjusted_timestamp()
            }
            
            if quantity:
                order_params['quantity'] = quantity
            if price and order_type != ORDER_TYPE_MARKET:
                order_params['price'] = price
                
            # Add any additional parameters
            order_params.update(kwargs)
            
            logger.info(f"Placing {side} {order_type} order for {symbol}")
            logger.debug(f"Order parameters: {order_params}")
            
            result = self.client.create_order(**order_params)
            logger.info(f"Order placed successfully: {result.get('orderId', 'Unknown')}")
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {e}")
            raise
        except BinanceOrderException as e:
            logger.error(f"Binance order error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order"""
        try:
            self._rate_limit()
            return self.client.cancel_order(symbol=symbol, orderId=int(order_id))
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
            return self.client.get_order(symbol=symbol, orderId=int(order_id))
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

    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get order history for all trading modes"""
        try:
            if config.binance.paper_trading:
                # Paper trading mode - return paper orders
                if hasattr(self.client, 'paper_orders'):
                    return self.client.paper_orders[-limit:] if self.client.paper_orders else []
                else:
                    return []
            elif config.binance.demo_mode:
                # Demo mode - return demo orders
                if hasattr(self.client, 'demo_orders'):
                    return getattr(self.client, 'demo_orders', [])[-limit:]
                else:
                    return []
            else:
                # Real trading mode - would get from database or API
                return []
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            return []

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
                
                filtered_symbols.append(symbol)
            
            # Sort by volume (descending) and limit results
            if min_volume_24h:
                tickers_dict = {t['symbol']: float(t.get('quoteVolume', 0)) for t in tickers}
                filtered_symbols.sort(key=lambda s: tickers_dict.get(s, 0), reverse=True)
            
            if max_symbols:
                filtered_symbols = filtered_symbols[:max_symbols]
            
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Failed to filter symbols: {e}")
            return []

    # Futures specific methods (only available in real trading mode)
    def futures_change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Change margin type for futures trading"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                logger.info(f"Simulated margin type change for {symbol} to {margin_type}")
                return {"code": 200, "msg": "success"}
            
            self._rate_limit()
            return self.client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
        except Exception as e:
            logger.error(f"Failed to change margin type: {e}")
            raise

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information from exchange info"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock symbol info for demo/paper trading
                return {
                    "symbol": symbol,
                    "status": "TRADING",
                    "baseAsset": symbol[:-4] if len(symbol) > 4 else symbol[:3],
                    "quoteAsset": symbol[-4:] if len(symbol) > 4 else symbol[3:],
                    "filters": []
                }
            
            exchange_info = self.client.futures_exchange_info()
            symbols = exchange_info.get('symbols', [])
            
            for symbol_info in symbols:
                if symbol_info.get('symbol') == symbol:
                    return symbol_info
            return None
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None

    def get_mark_price(self, symbol: str) -> Dict[str, Any]:
        """Get mark price for futures symbol"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock mark price for demo/paper trading
                ticker = self.get_ticker_price(symbol)
                price = float(ticker.get('price', 0)) if ticker else 0
                return {"symbol": symbol, "markPrice": str(price)}
            
            self._rate_limit()
            return self.client.futures_mark_price(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get mark price for {symbol}: {e}")
            raise

    def get_funding_rate(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get funding rate history"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock funding rate for demo/paper trading
                return [{"symbol": symbol, "fundingRate": "0.0001", "fundingTime": int(time.time() * 1000)}]
            
            self._rate_limit()
            result = self.client.futures_funding_rate(symbol=symbol, limit=limit)
            return result if isinstance(result, list) else [result]
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            return []

    def get_futures_account(self) -> Dict[str, Any]:
        """Get futures account information"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock futures account for demo/paper trading
                return {
                    "totalWalletBalance": "10000.00000000",
                    "totalUnrealizedProfit": "0.00000000",
                    "totalMarginBalance": "10000.00000000",
                    "totalPositionInitialMargin": "0.00000000",
                    "totalOpenOrderInitialMargin": "0.00000000",
                    "maxWithdrawAmount": "10000.00000000",
                    "assets": [
                        {
                            "asset": "USDT",
                            "walletBalance": "10000.00000000",
                            "unrealizedProfit": "0.00000000"
                        }
                    ]
                }
            
            self._rate_limit()
            return self.client.futures_account()
        except Exception as e:
            logger.error(f"Failed to get futures account: {e}")
            raise

    def get_all_symbols_info(self) -> List[Dict[str, Any]]:
        """Get information for all symbols"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock symbols for demo/paper trading
                mock_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT"]
                return [
                    {
                        "symbol": symbol,
                        "status": "TRADING",
                        "baseAsset": symbol[:-4] if len(symbol) > 4 else symbol[:3],
                        "quoteAsset": symbol[-4:] if len(symbol) > 4 else symbol[3:],
                        "filters": []
                    }
                    for symbol in mock_symbols
                ]
            
            self._rate_limit()
            exchange_info = self.client.futures_exchange_info()
            return exchange_info.get('symbols', [])
        except Exception as e:
            logger.error(f"Failed to get all symbols info: {e}")
            return []

    def get_futures_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get futures positions"""
        try:
            if config.binance.demo_mode or config.binance.paper_trading:
                # Return mock positions for demo/paper trading
                if symbol:
                    return [{
                        "symbol": symbol,
                        "positionAmt": "0.000",
                        "entryPrice": "0.0000",
                        "markPrice": "0.0000",
                        "unRealizedProfit": "0.0000",
                        "liquidationPrice": "0",
                        "leverage": "20",
                        "maxNotionalValue": "1000000",
                        "marginType": "cross",
                        "isolatedMargin": "0.00000000",
                        "isAutoAddMargin": "false",
                        "positionSide": "BOTH",
                        "notional": "0",
                        "isolatedWallet": "0"
                    }]
                else:
                    return []
            
            self._rate_limit()
            return self.client.futures_position_information(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get futures positions: {e}")
            return []

    def calculate_quantity(self, symbol: str, position_size: float, current_price: float) -> float:
        """計算交易數量，基於持倉大小和當前價格"""
        try:
            # 獲取交易對資訊
            exchange_info = self.get_exchange_info()
            symbol_info = None
            
            for s in exchange_info.get('symbols', []):
                if s.get('symbol') == symbol:
                    symbol_info = s
                    break
            
            if not symbol_info:
                logger.error(f"Symbol {symbol} not found in exchange info")
                return 0.0
            
            # 獲取最小數量限制
            min_qty = 0.0
            step_size = 0.0
            
            for filter_item in symbol_info.get('filters', []):
                if filter_item.get('filterType') == 'LOT_SIZE':
                    min_qty = float(filter_item.get('minQty', 0))
                    step_size = float(filter_item.get('stepSize', 0))
                    break
            
            # 計算基礎數量（基於持倉大小的USD價值）
            if current_price > 0:
                base_quantity = position_size / current_price
            else:
                return 0.0
            
            # 調整到符合步長要求
            if step_size > 0:
                quantity = round(base_quantity / step_size) * step_size
            else:
                quantity = base_quantity
            
            # 確保不小於最小數量
            if quantity < min_qty:
                quantity = min_qty
            
            return quantity
            
        except Exception as e:
            logger.error(f"Failed to calculate quantity for {symbol}: {e}")
            return 0.0

# Create global instance for backwards compatibility
# This will be initialized when first imported
try:
    binance_client = BinanceClient()
except Exception as e:
    logger.warning(f"Failed to create global binance_client instance: {e}")
    binance_client = None

# Factory function for getting client instances
def get_client(trading_type: Optional[str] = None) -> Optional[BinanceClient]:
    """Get a client instance for the specified trading type"""
    try:
        if trading_type == "futures":
            return BinanceClient("futures")
        elif trading_type == "spot":
            return BinanceClient("spot")
        else:
            # Return the global instance or create a new one
            return binance_client if binance_client else BinanceClient()
    except Exception as e:
        logger.error(f"Failed to create {trading_type} client: {e}")
        return None
