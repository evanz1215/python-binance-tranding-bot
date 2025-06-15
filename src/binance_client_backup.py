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
                from .paper_trading_client import PaperTradingClient
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
        """獲取調整後的時間戳"""
        return int(time.time() * 1000) + self.time_offset
    
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

    # ==================== 合約交易功能 ====================
    
    def get_futures_account(self) -> Dict[str, Any]:
        """Get futures account information"""
        try:
            self._rate_limit()
            return self.client.futures_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get futures account: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get futures account: {e}")
            raise
    
    def get_futures_balance(self, asset: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get futures account balance"""
        try:
            account = self.get_futures_account()
            balances = {}
            
            for balance in account.get('assets', []):
                asset_name = balance['asset']
                wallet_balance = float(balance['walletBalance'])
                unrealized_pnl = float(balance['unrealizedProfit'])
                margin_balance = float(balance['marginBalance'])
                available_balance = float(balance['availableBalance'])
                
                if wallet_balance > 0 or unrealized_pnl != 0:
                    balances[asset_name] = {
                        'wallet_balance': wallet_balance,
                        'unrealized_pnl': unrealized_pnl,
                        'margin_balance': margin_balance,
                        'available_balance': available_balance
                    }
            
            if asset:
                return balances.get(asset, {
                    'wallet_balance': 0.0,
                    'unrealized_pnl': 0.0,
                    'margin_balance': 0.0,
                    'available_balance': 0.0
                })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get futures balance: {e}")
            raise
    
    def get_futures_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get futures positions"""
        try:
            self._rate_limit()
            positions = self.client.futures_position_information(symbol=symbol)
            
            # 只返回有持倉的位置
            active_positions = []
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    active_positions.append({
                        'symbol': pos['symbol'],
                        'position_side': pos['positionSide'],
                        'position_amt': position_amt,
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'percentage': float(pos['percentage']),
                        'notional': float(pos['notional']),
                        'isolated_wallet': float(pos['isolatedWallet']),
                        'update_time': pos['updateTime']
                    })
            
            return active_positions
        except Exception as e:
            logger.error(f"Failed to get futures positions: {e}")
            raise
    
    def place_futures_order(self, symbol: str, side: str, order_type: str, 
                           quantity: float, price: Optional[float] = None,
                           position_side: str = "BOTH", reduce_only: bool = False,
                           time_in_force: str = "GTC", **kwargs) -> Dict[str, Any]:
        """Place a futures order"""
        try:
            self._rate_limit()
            
            order_params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'positionSide': position_side,
                'timeInForce': time_in_force,
                'reduceOnly': reduce_only
            }
            
            if price and order_type in ['LIMIT', 'STOP', 'TAKE_PROFIT']:
                order_params['price'] = price
            
            # 添加其他參數
            order_params.update(kwargs)
            
            logger.info(f"Placing futures order: {order_params}")
            
            if config.binance.testnet:
                return self.client.futures_create_order(**order_params)
            else:
                # 實盤交易時的額外安全檢查
                return self.client.futures_create_order(**order_params)
                
        except BinanceOrderException as e:
            logger.error(f"Futures order failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place futures order: {e}")
            raise
    
    def cancel_futures_order(self, symbol: str, order_id: Optional[str] = None, 
                            orig_client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Cancel a futures order"""
        try:
            self._rate_limit()
            params = {'symbol': symbol}
            
            if order_id:
                params['orderId'] = order_id
            elif orig_client_order_id:
                params['origClientOrderId'] = orig_client_order_id
            else:
                raise ValueError("Either order_id or orig_client_order_id must be provided")
            
            return self.client.futures_cancel_order(**params)
        except Exception as e:
            logger.error(f"Failed to cancel futures order: {e}")
            raise
    
    def get_futures_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open futures orders"""
        try:
            self._rate_limit()
            orders = self.client.futures_get_open_orders(symbol=symbol)
            return orders if isinstance(orders, list) else [orders] if orders else []
        except Exception as e:
            logger.error(f"Failed to get futures open orders: {e}")
            raise
    
    def change_futures_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Change leverage for a futures symbol"""
        try:
            self._rate_limit()
            return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
        except Exception as e:
            logger.error(f"Failed to change leverage for {symbol}: {e}")
            raise
    
    def change_futures_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Change margin type (ISOLATED or CROSSED) for a futures symbol"""
        try:
            self._rate_limit()
            return self.client.futures_change_margin_type(symbol=symbol, marginType=margin_type)
        except Exception as e:
            logger.error(f"Failed to change margin type for {symbol}: {e}")
            raise
    
    def get_futures_symbol_info(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get futures symbol information"""
        try:
            self._rate_limit()
            exchange_info = self.client.futures_exchange_info()
            
            if symbol:
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        return s
                raise ValueError(f"Futures symbol {symbol} not found")
            
            return exchange_info['symbols']
        except Exception as e:
            logger.error(f"Failed to get futures symbol info: {e}")
            raise
    
    def get_futures_mark_price(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get futures mark price"""
        try:
            self._rate_limit()
            return self.client.futures_mark_price(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get futures mark price: {e}")
            raise
    
    def get_futures_funding_rate(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get funding rate history"""
        try:
            self._rate_limit()
            result = self.client.futures_funding_rate(symbol=symbol, limit=limit)
            return result if isinstance(result, list) else [result] if result else []
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            raise
    
    def calculate_futures_quantity(self, symbol: str, usdt_amount: float, 
                                  leverage: int, price: float) -> float:
        """Calculate futures quantity based on USDT amount, leverage and price"""
        try:
            symbol_info = self.get_futures_symbol_info(symbol)
            if not symbol_info or isinstance(symbol_info, list):
                raise ValueError(f"Futures symbol {symbol} not found")
            
            # 獲取數量過濾器
            quantity_precision = 0
            min_qty = 0.0
            step_size = 1.0
            
            for f in symbol_info.get('filters', []):
                if f.get('filterType') == 'LOT_SIZE':
                    min_qty = float(f.get('minQty', 0))
                    step_size = float(f.get('stepSize', 1))
                    # 計算精度
                    step_str = f.get('stepSize', '1')
                    if '.' in step_str:
                        quantity_precision = len(step_str.split('.')[1].rstrip('0'))
                    break
            
            # 計算合約數量（考慮槓桿）
            notional_value = usdt_amount * leverage
            quantity = notional_value / price
            
            # 調整到合適的步長
            quantity = round(quantity / step_size) * step_size
            
            # 確保最小數量
            if quantity < min_qty:
                raise ValueError(f"Calculated quantity {quantity} is less than minimum {min_qty}")
            
            # 調整精度
            quantity = round(quantity, quantity_precision)
            
            return quantity
            
        except Exception as e:
            logger.error(f"Failed to calculate futures quantity: {e}")
            raise


# Global client instances
try:
    # 根據配置的交易模式初始化客戶端
    trading_mode = config.binance.trading_mode
    
    if trading_mode == "both":
        # 如果配置為同時使用現貨和合約，優先使用合約客戶端
        binance_client = BinanceClient("futures") if config.binance.has_valid_credentials("futures") else BinanceClient("spot")
        spot_client = BinanceClient("spot") if config.binance.has_valid_credentials("spot") else None
        futures_client = BinanceClient("futures") if config.binance.has_valid_credentials("futures") else None
    elif trading_mode == "spot":
        binance_client = BinanceClient("spot")
        spot_client = binance_client
        futures_client = None
    else:  # futures
        binance_client = BinanceClient("futures")
        spot_client = None
        futures_client = binance_client
        
    logger.info(f"Initialized Binance clients for {trading_mode} trading")
    
except (ImportError, ValueError) as e:
    logger.warning(f"BinanceClient initialization failed: {e}")
    binance_client = None
    spot_client = None
    futures_client = None


def get_client(trading_type: Optional[str] = None):
    """獲取指定類型的客戶端"""
    if trading_type == "spot":
        return spot_client
    elif trading_type == "futures":
        return futures_client
    else:
        return binance_client
