#!/usr/bin/env python3
"""
Demo 模式模擬客戶端 - 提供模擬交易功能
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from loguru import logger


class DemoModeClient:
    """Demo 模式模擬 Binance 客戶端"""
    
    def __init__(self):
        self.demo_balance = {
            'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0}
        }
        self.demo_positions = {}
        self.demo_orders = []
        self.order_id_counter = 1000
        
        logger.info("🎮 Demo 模式已啟動 - 所有交易都是模擬的")
    
    def get_server_time(self) -> Dict[str, Any]:
        """模擬獲取伺服器時間"""
        return {
            'serverTime': int(time.time() * 1000)
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """模擬獲取帳戶信息"""
        balances = []
        for asset, balance in self.demo_balance.items():
            balances.append({
                'asset': asset,
                'free': str(balance['free']),
                'locked': str(balance['locked'])
            })
        
        return {
            'balances': balances,
            'canTrade': True,
            'canWithdraw': True,
            'canDeposit': True
        }
    
    def get_balance(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """模擬獲取餘額"""
        if asset:
            return self.demo_balance.get(asset, {'free': 0.0, 'locked': 0.0, 'total': 0.0})
        return self.demo_balance
    
    def get_futures_account(self) -> Dict[str, Any]:
        """模擬獲取合約帳戶信息"""
        total_balance = sum(balance['total'] for balance in self.demo_balance.values())
        
        assets = []
        for asset, balance in self.demo_balance.items():
            assets.append({
                'asset': asset,
                'walletBalance': str(balance['total']),
                'unrealizedProfit': '0.00000000',
                'marginBalance': str(balance['total']),
                'availableBalance': str(balance['free'])
            })
        
        return {
            'totalWalletBalance': str(total_balance),
            'totalUnrealizedProfit': '0.00000000',
            'totalMarginBalance': str(total_balance),
            'totalInitialMargin': '0.00000000',
            'totalMaintMargin': '0.00000000',
            'availableBalance': str(sum(balance['free'] for balance in self.demo_balance.values())),
            'assets': assets
        }
    
    def get_futures_balance(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """模擬獲取合約餘額"""
        if asset:
            balance = self.demo_balance.get(asset, {'free': 0.0, 'locked': 0.0, 'total': 0.0})
            return {
                'wallet_balance': balance['total'],
                'unrealized_pnl': 0.0,
                'margin_balance': balance['total'],
                'available_balance': balance['free']
            }
        return self.demo_balance
    
    def get_futures_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """模擬獲取合約持倉"""
        positions = []
        for pos_symbol, position in self.demo_positions.items():
            if symbol is None or pos_symbol == symbol:
                positions.append({
                    'symbol': pos_symbol,
                    'positionAmt': str(position['quantity']),
                    'entryPrice': str(position['entry_price']),
                    'markPrice': str(position['mark_price']),
                    'unRealizedProfit': str(position['unrealized_pnl']),
                    'positionSide': position['side']
                })
        return positions
    
    def get_24hr_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """模擬獲取 24 小時價格統計"""
        if symbol:
            # 模擬價格數據
            base_price = self._get_demo_price(symbol)
            return {
                'symbol': symbol,
                'lastPrice': str(base_price),
                'priceChange': str(random.uniform(-100, 100)),
                'priceChangePercent': str(random.uniform(-5, 5)),
                'volume': str(random.uniform(1000000, 10000000)),
                'quoteVolume': str(random.uniform(50000000, 500000000))
            }
        else:
            # 返回多個交易對的數據
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
            return [self.get_24hr_ticker(s) for s in symbols]
    
    def get_klines(self, **params) -> List[List[str]]:
        """模擬獲取 K 線數據"""
        symbol = params.get('symbol', 'BTCUSDT')
        interval = params.get('interval', '1h')
        limit = params.get('limit', 100)
        
        base_price = self._get_demo_price(symbol)
        klines = []
        
        for i in range(limit):
            timestamp = int(time.time() * 1000) - (limit - i) * 3600000  # 每小時
            open_price = base_price + random.uniform(-100, 100)
            close_price = open_price + random.uniform(-50, 50)
            high_price = max(open_price, close_price) + random.uniform(0, 20)
            low_price = min(open_price, close_price) - random.uniform(0, 20)
            volume = random.uniform(100, 1000)
            
            klines.append([
                str(timestamp),
                str(open_price),
                str(high_price),
                str(low_price),
                str(close_price),
                str(volume),
                str(timestamp + 3600000),
                str(volume * close_price),
                str(random.randint(100, 1000)),
                str(volume * 0.8),
                str(volume * close_price * 0.8),
                '0'
            ])
        
        return klines
    
    def create_order(self, **params) -> Dict[str, Any]:
        """模擬創建現貨訂單"""
        return self._create_demo_order(**params)
    
    def futures_create_order(self, **params) -> Dict[str, Any]:
        """模擬創建合約訂單"""
        return self._create_demo_order(**params)
    
    def _create_demo_order(self, **params) -> Dict[str, Any]:
        """創建模擬訂單"""
        symbol = params.get('symbol', 'BTCUSDT')
        side = params.get('side', 'BUY')
        order_type = params.get('type', 'MARKET')
        quantity = float(params.get('quantity', 0))
        price = float(params.get('price', 0)) if params.get('price') else self._get_demo_price(symbol)
        
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        # 模擬訂單執行
        executed_qty = quantity
        executed_price = price
        commission = executed_qty * executed_price * 0.001  # 0.1% 手續費
        
        order = {
            'orderId': order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'origQty': str(quantity),
            'executedQty': str(executed_qty),
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'price': str(price),
            'fills': [{
                'price': str(executed_price),
                'qty': str(executed_qty),
                'commission': str(commission),
                'commissionAsset': 'USDT'
            }],
            'transactTime': int(time.time() * 1000)
        }
        
        # 更新模擬餘額和持倉
        self._update_demo_balance(order)
        
        logger.info(f"🎮 模擬訂單執行: {side} {executed_qty} {symbol} @ {executed_price}")
        
        return order
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """模擬獲取開放訂單"""
        # Demo 模式下假設所有訂單都已執行
        return []
    
    def cancel_order(self, **params) -> Dict[str, Any]:
        """模擬取消訂單"""
        return {
            'orderId': params.get('orderId', 0),
            'symbol': params.get('symbol', ''),
            'status': 'CANCELED'
        }
    
    def _get_demo_price(self, symbol: str) -> float:
        """獲取模擬價格"""
        base_prices = {
            'BTCUSDT': 45000.0,
            'ETHUSDT': 3000.0,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8.0,
            'LINKUSDT': 15.0
        }
        base = base_prices.get(symbol, 100.0)
        # 添加一些隨機波動
        return base + random.uniform(-base * 0.02, base * 0.02)
    
    def _update_demo_balance(self, order: Dict[str, Any]) -> None:
        """更新模擬餘額"""
        symbol = order['symbol']
        side = order['side']
        executed_qty = float(order['executedQty'])
        executed_price = float(order['fills'][0]['price'])
        commission = float(order['fills'][0]['commission'])
        
        # 簡化實現：只處理 USDT 交易對
        if side == 'BUY':
            # 買入：減少 USDT，增加持倉
            cost = executed_qty * executed_price + commission
            if 'USDT' in self.demo_balance:
                self.demo_balance['USDT']['free'] -= cost
                self.demo_balance['USDT']['total'] -= cost
            
            # 更新持倉
            if symbol not in self.demo_positions:
                self.demo_positions[symbol] = {
                    'quantity': 0,
                    'entry_price': 0,
                    'mark_price': executed_price,
                    'unrealized_pnl': 0,
                    'side': 'LONG'
                }
            
            pos = self.demo_positions[symbol]
            total_cost = pos['quantity'] * pos['entry_price'] + executed_qty * executed_price
            pos['quantity'] += executed_qty
            pos['entry_price'] = total_cost / pos['quantity'] if pos['quantity'] > 0 else executed_price
            pos['mark_price'] = executed_price
            
        elif side == 'SELL':
            # 賣出：增加 USDT，減少持倉
            revenue = executed_qty * executed_price - commission
            if 'USDT' in self.demo_balance:
                self.demo_balance['USDT']['free'] += revenue
                self.demo_balance['USDT']['total'] += revenue
            
            # 更新持倉
            if symbol in self.demo_positions:
                self.demo_positions[symbol]['quantity'] -= executed_qty
                if self.demo_positions[symbol]['quantity'] <= 0:
                    del self.demo_positions[symbol]

    # ========== Binance Client 兼容方法別名 ==========
    
    def get_account(self) -> Dict[str, Any]:
        """別名：get_account_info"""
        return self.get_account_info()
    
    def get_ticker(self, symbol: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """別名：get_24hr_ticker"""
        return self.get_24hr_ticker(symbol)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """模擬交易所信息"""
        return {
            'symbols': [
                {'symbol': 'BTCUSDT', 'status': 'TRADING'},
                {'symbol': 'ETHUSDT', 'status': 'TRADING'},
                {'symbol': 'ADAUSDT', 'status': 'TRADING'}
            ]
        }
    
    def get_order(self, symbol: str, orderId: int) -> Dict[str, Any]:
        """模擬查詢訂單"""
        return {
            'orderId': orderId,
            'symbol': symbol,
            'status': 'FILLED',
            'side': 'BUY',
            'type': 'MARKET'
        }
    
    def get_my_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """模擬交易歷史"""
        return []
    
    def futures_account(self) -> Dict[str, Any]:
        """別名：get_futures_account"""
        return self.get_futures_account()
    
    def futures_position_information(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """別名：get_futures_positions"""
        return self.get_futures_positions(symbol)
    
    def futures_cancel_order(self, **params) -> Dict[str, Any]:
        """模擬取消合約訂單"""
        return self.cancel_order(**params)
    
    def futures_get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """別名：get_open_orders for futures"""
        return self.get_open_orders(symbol)
    
    def futures_change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """模擬設置槓桿"""
        return {
            'symbol': symbol,
            'leverage': leverage,
            'maxNotionalValue': '1000000'
        }


# 全域 demo 客戶端實例
demo_client = DemoModeClient()
