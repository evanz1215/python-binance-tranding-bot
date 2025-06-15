#!/usr/bin/env python3
"""
紙上交易客戶端 - 使用真實 API 數據但虛擬資金
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from loguru import logger

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
    BINANCE_AVAILABLE = True
except ImportError:
    Client = None
    BINANCE_AVAILABLE = False

from .config import config


class PaperTradingClient:
    """紙上交易客戶端 - 真實數據，虛擬交易"""
    
    def __init__(self, trading_type: str = "futures"):
        """初始化紙上交易客戶端"""
        self.trading_type = trading_type.lower()
        
        # 初始化真實 API 客戶端用於獲取市場數據
        if not BINANCE_AVAILABLE:
            raise ImportError("python-binance package is required for paper trading")
        
        # 獲取 API 憑證
        api_key, secret_key = config.binance.get_api_credentials(self.trading_type)
        
        if not api_key or not secret_key:
            raise ValueError(f"Missing API credentials for {self.trading_type} paper trading")
        
        # 創建真實 API 客戶端（只用於市場數據）
        self.real_client = Client(
            api_key,
            secret_key,
            testnet=config.binance.testnet
        )
        
        # 虛擬帳戶數據
        self.paper_balance = {
            'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0}
        }
        self.paper_positions = {}
        self.paper_orders = []
        self.order_id_counter = 10000
        self.trade_history = []
        
        # 時間同步
        self.time_offset = config.binance.time_offset
        try:
            server_time = self.real_client.get_server_time()
            local_time = int(time.time() * 1000) + self.time_offset
            calculated_offset = server_time['serverTime'] - local_time
            logger.info(f"Paper trading - Server time offset: {calculated_offset}ms")
        except Exception as e:
            logger.warning(f"Failed to sync server time: {e}")
        
        self.last_request_time = 0
        self.request_interval = 0.1
        
        logger.info(f"📋 紙上交易模式已啟動 - 使用真實 {self.trading_type} 市場數據，虛擬資金交易")
    
    def _rate_limit(self):
        """簡單的請求頻率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_interval:
            time.sleep(self.request_interval - time_since_last)
        self.last_request_time = time.time()
    
    # ========== 真實市場數據方法 ==========
      def get_server_time(self) -> Dict[str, Any]:
        """獲取真實伺服器時間"""
        self._rate_limit()
        return self.real_client.get_server_time()
    
    def get_24hr_ticker(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """獲取真實 24 小時價格統計"""
        self._rate_limit()
        try:
            if symbol:
                return self.real_client.get_ticker(symbol=symbol)
            else:
                return self.real_client.get_ticker()
        except BinanceAPIException as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def get_klines(self, **params) -> List[List[str]]:
        """獲取真實 K 線數據"""
        self._rate_limit()
        try:
            symbol = params.get('symbol')
            interval = params.get('interval', '1h')
            limit = params.get('limit', 100)
            start_time = params.get('startTime')
            end_time = params.get('endTime')
            
            klines = self.real_client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=int(start_time.timestamp() * 1000) if start_time else None,
                endTime=int(end_time.timestamp() * 1000) if end_time else None
            )
            
            return klines
        except BinanceAPIException as e:
            logger.error(f"Failed to get klines: {e}")
            raise
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """獲取真實交易所信息"""
        self._rate_limit()
        try:
            return self.real_client.get_exchange_info()
        except BinanceAPIException as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    # ========== 虛擬帳戶和交易方法 ==========
    
    def get_account_info(self) -> Dict[str, Any]:
        """獲取虛擬帳戶信息"""
        balances = []
        for asset, balance in self.paper_balance.items():
            if balance['total'] > 0:
                balances.append({
                    'asset': asset,
                    'free': str(balance['free']),
                    'locked': str(balance['locked'])
                })
        
        return {
            'balances': balances,
            'canTrade': True,
            'canWithdraw': False,  # 紙上交易不能提現
            'canDeposit': False,   # 紙上交易不能充值
            'updateTime': int(time.time() * 1000)
        }
    
    def get_balance(self, asset: Optional[str] = None) -> Union[Dict[str, float], Dict[str, Dict[str, float]]]:
        """獲取虛擬餘額"""
        if asset:
            return self.paper_balance.get(asset, {'free': 0.0, 'locked': 0.0, 'total': 0.0})
        return self.paper_balance
    
    def get_futures_account(self) -> Dict[str, Any]:
        """獲取虛擬合約帳戶信息"""
        total_balance = sum(balance['total'] for balance in self.paper_balance.values())
        unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.paper_positions.values())
        
        assets = []
        for asset, balance in self.paper_balance.items():
            assets.append({
                'asset': asset,
                'walletBalance': str(balance['total']),
                'unrealizedProfit': str(unrealized_pnl),
                'marginBalance': str(balance['total'] + unrealized_pnl),
                'availableBalance': str(balance['free'])
            })
        
        return {
            'totalWalletBalance': str(total_balance),
            'totalUnrealizedProfit': str(unrealized_pnl),
            'totalMarginBalance': str(total_balance + unrealized_pnl),
            'totalInitialMargin': '0.00000000',
            'totalMaintMargin': '0.00000000',
            'availableBalance': str(sum(balance['free'] for balance in self.paper_balance.values())),
            'assets': assets,
            'updateTime': int(time.time() * 1000)
        }
    
    def get_futures_balance(self, asset: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """獲取虛擬合約餘額"""
        if asset:
            balance = self.paper_balance.get(asset, {'free': 0.0, 'locked': 0.0, 'total': 0.0})
            unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.paper_positions.values() 
                                if pos.get('asset') == asset)
            return {
                'wallet_balance': balance['total'],
                'unrealized_pnl': unrealized_pnl,
                'margin_balance': balance['total'] + unrealized_pnl,
                'available_balance': balance['free']
            }
        return self.paper_balance
    
    def get_futures_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取虛擬合約持倉"""
        # 先更新持倉的當前價格和未實現盈虧
        self._update_positions_pnl()
        
        positions = []
        for pos_symbol, position in self.paper_positions.items():
            if symbol is None or pos_symbol == symbol:
                positions.append({
                    'symbol': pos_symbol,
                    'positionAmt': str(position['quantity']),
                    'entryPrice': str(position['entry_price']),
                    'markPrice': str(position['mark_price']),
                    'unRealizedProfit': str(position['unrealized_pnl']),
                    'positionSide': position['side'],
                    'updateTime': int(time.time() * 1000)
                })
        return positions
    
    def create_order(self, **params) -> Dict[str, Any]:
        """創建虛擬現貨訂單"""
        return self._create_paper_order('spot', **params)
    
    def futures_create_order(self, **params) -> Dict[str, Any]:
        """創建虛擬合約訂單"""
        return self._create_paper_order('futures', **params)
    
    def _create_paper_order(self, order_type: str, **params) -> Dict[str, Any]:
        """創建虛擬訂單"""
        symbol = params.get('symbol', 'BTCUSDT')
        side = params.get('side', 'BUY')
        order_type_param = params.get('type', 'MARKET')
        quantity = float(params.get('quantity', 0))
        price = float(params.get('price', 0)) if params.get('price') else None
        
        # 獲取當前真實市場價格
        try:
            ticker = self.get_24hr_ticker(symbol)
            current_price = float(ticker['lastPrice'])
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            current_price = price or 50000.0  # 默認價格
        
        # 確定執行價格
        if order_type_param == 'MARKET':
            executed_price = current_price
        else:
            executed_price = price or current_price
        
        # 生成訂單 ID
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        # 計算手續費
        commission = quantity * executed_price * 0.001  # 0.1% 手續費
        
        # 檢查餘額是否足夠
        if side == 'BUY':
            required_amount = quantity * executed_price + commission
            usdt_balance = self.paper_balance.get('USDT', {}).get('free', 0)
            if usdt_balance < required_amount:
                raise ValueError(f"Insufficient balance. Required: {required_amount}, Available: {usdt_balance}")
        
        # 創建訂單記錄
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type_param,
            'origQty': str(quantity),
            'executedQty': str(quantity),
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'price': str(executed_price),
            'fills': [{
                'price': str(executed_price),
                'qty': str(quantity),
                'commission': str(commission),
                'commissionAsset': 'USDT'
            }],
            'transactTime': int(time.time() * 1000)
        }
        
        # 更新虛擬餘額和持倉
        self._update_paper_balance(order)
        
        # 記錄交易歷史
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': executed_price,
            'commission': commission,
            'order_type': order_type_param,
            'trade_type': order_type
        }
        self.trade_history.append(trade_record)
        
        logger.info(f"📋 紙上交易執行: {side} {quantity} {symbol} @ ${executed_price:.2f} (手續費: ${commission:.4f})")
        
        return order
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取虛擬開放訂單（紙上交易中通常為空，因為都是市價單立即執行）"""
        return []
    
    def cancel_order(self, **params) -> Dict[str, Any]:
        """取消虛擬訂單"""
        return {
            'orderId': params.get('orderId', 0),
            'symbol': params.get('symbol', ''),
            'status': 'CANCELED'
        }
    
    def _update_paper_balance(self, order: Dict[str, Any]) -> None:
        """更新虛擬餘額和持倉"""
        symbol = order['symbol']
        side = order['side']
        quantity = float(order['executedQty'])
        price = float(order['fills'][0]['price'])
        commission = float(order['fills'][0]['commission'])
        
        # 更新 USDT 餘額
        if side == 'BUY':
            # 買入：減少 USDT
            cost = quantity * price + commission
            if 'USDT' in self.paper_balance:
                self.paper_balance['USDT']['free'] -= cost
                self.paper_balance['USDT']['total'] -= cost
            
            # 更新持倉
            if symbol not in self.paper_positions:
                self.paper_positions[symbol] = {
                    'quantity': 0,
                    'entry_price': 0,
                    'mark_price': price,
                    'unrealized_pnl': 0,
                    'side': 'LONG',
                    'asset': symbol.replace('USDT', '')
                }
            
            pos = self.paper_positions[symbol]
            total_cost = pos['quantity'] * pos['entry_price'] + quantity * price
            pos['quantity'] += quantity
            pos['entry_price'] = total_cost / pos['quantity'] if pos['quantity'] > 0 else price
            pos['mark_price'] = price
            
        elif side == 'SELL':
            # 賣出：增加 USDT
            revenue = quantity * price - commission
            if 'USDT' in self.paper_balance:
                self.paper_balance['USDT']['free'] += revenue
                self.paper_balance['USDT']['total'] += revenue
            
            # 更新持倉
            if symbol in self.paper_positions:
                self.paper_positions[symbol]['quantity'] -= quantity
                if self.paper_positions[symbol]['quantity'] <= 0:
                    del self.paper_positions[symbol]
    
    def _update_positions_pnl(self) -> None:
        """更新持倉的未實現盈虧"""
        for symbol, position in self.paper_positions.items():
            try:
                # 獲取當前市場價格
                ticker = self.get_24hr_ticker(symbol)
                current_price = float(ticker['lastPrice'])
                
                # 更新標記價格
                position['mark_price'] = current_price
                
                # 計算未實現盈虧
                entry_price = position['entry_price']
                quantity = position['quantity']
                pnl = (current_price - entry_price) * quantity
                position['unrealized_pnl'] = pnl
                
            except Exception as e:
                logger.warning(f"Failed to update PnL for {symbol}: {e}")
                position['unrealized_pnl'] = 0
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """獲取交易歷史"""
        return self.trade_history
    
    def get_paper_trading_stats(self) -> Dict[str, Any]:
        """獲取紙上交易統計"""
        total_trades = len(self.trade_history)
        total_commission = sum(trade['commission'] for trade in self.trade_history)
        
        # 計算總盈虧
        current_balance = sum(balance['total'] for balance in self.paper_balance.values())
        unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in self.paper_positions.values())
        total_value = current_balance + unrealized_pnl
        initial_balance = 10000.0  # 初始資金
        total_pnl = total_value - initial_balance
        
        return {
            'initial_balance': initial_balance,
            'current_balance': current_balance,
            'unrealized_pnl': unrealized_pnl,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'total_commission': total_commission,
            'active_positions': len(self.paper_positions),
            'pnl_percentage': (total_pnl / initial_balance) * 100
        }

    # ========== Binance Client 兼容方法別名 ==========
    
    def get_account(self) -> Dict[str, Any]:
        """別名：get_account_info"""
        return self.get_account_info()
    
    def get_ticker(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """別名：get_24hr_ticker"""
        return self.get_24hr_ticker(symbol)
    
    def get_order(self, symbol: str, orderId: int) -> Dict[str, Any]:
        """查詢虛擬訂單"""
        for order in self.paper_orders:
            if order['symbol'] == symbol and order['orderId'] == orderId:
                return order
        
        # 如果找不到，返回默認訂單
        return {
            'orderId': orderId,
            'symbol': symbol,
            'status': 'FILLED',
            'side': 'BUY',
            'type': 'MARKET',
            'executedQty': '0',
            'price': '0'
        }
    
    def get_my_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """獲取虛擬交易歷史"""
        trades = []
        for order in self.paper_orders[-limit:]:
            if order['symbol'] == symbol and order['status'] == 'FILLED':
                trades.append({
                    'id': order['orderId'],
                    'symbol': order['symbol'],
                    'orderId': order['orderId'],
                    'side': order['side'],
                    'qty': order['executedQty'],
                    'price': order['price'],
                    'commission': order.get('commission', '0'),
                    'time': order.get('transactTime', int(time.time() * 1000))
                })
        return trades
    
    def futures_account(self) -> Dict[str, Any]:
        """別名：get_futures_account"""
        return self.get_futures_account()
    
    def futures_position_information(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """別名：get_futures_positions"""
        return self.get_futures_positions(symbol)
    
    def futures_cancel_order(self, **params) -> Dict[str, Any]:
        """取消虛擬合約訂單"""
        symbol = params.get('symbol')
        order_id = params.get('orderId')
        
        for order in self.paper_orders:
            if order['symbol'] == symbol and order['orderId'] == order_id:
                order['status'] = 'CANCELED'
                return order
        
        return {
            'orderId': order_id,
            'symbol': symbol,
            'status': 'CANCELED'
        }
    
    def futures_get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """別名：get_open_orders for futures"""
        return self.get_open_orders(symbol)
    
    def futures_change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """設置虛擬槓桿"""
        logger.info(f"Setting leverage for {symbol} to {leverage}x (paper trading)")
        return {
            'symbol': symbol,
            'leverage': leverage,
            'maxNotionalValue': '1000000'
        }
        

# 全域紙上交易客戶端實例（如果啟用）
paper_trading_client = None
if config.binance.paper_trading:
    try:
        paper_trading_client = PaperTradingClient()
    except Exception as e:
        logger.error(f"Failed to initialize paper trading client: {e}")
        paper_trading_client = None
