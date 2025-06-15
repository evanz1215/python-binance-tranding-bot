#!/usr/bin/env python3
"""
測試 Paper Trading 訂單功能
"""
import requests
import json
from datetime import datetime

def test_orders_api():
    """測試訂單 API 功能"""
    base_url = "http://localhost:8000"
    
    print("🧪 測試 Paper Trading 訂單 API 功能")
    print("=" * 50)
    
    # 1. 測試訂單摘要
    try:
        response = requests.get(f"{base_url}/api/orders/summary")
        if response.status_code == 200:
            summary = response.json()
            print("✅ 訂單摘要:")
            print(f"  📊 交易模式: {summary.get('trading_mode', 'N/A')}")
            print(f"  📋 未完成訂單: {summary.get('open_orders', 0)}")
            print(f"  💰 今日交易: {summary.get('todays_trades', 0)}")
            print(f"  💵 總交易量: ${summary.get('total_volume', 0):,.2f}")
        else:
            print(f"❌ 訂單摘要失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 訂單摘要錯誤: {e}")
    
    print()
    
    # 2. 測試未完成訂單
    try:
        response = requests.get(f"{base_url}/api/orders/open")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ 未完成訂單: {len(orders)} 筆")
            for order in orders[:3]:  # 顯示前3筆
                print(f"  📋 {order.get('symbol')} {order.get('side')} {order.get('origQty')} @ ${order.get('price')}")
        else:
            print(f"❌ 未完成訂單失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 未完成訂單錯誤: {e}")
    
    print()
    
    # 3. 測試訂單歷史
    try:
        response = requests.get(f"{base_url}/api/orders/history?limit=10")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ 訂單歷史: {len(orders)} 筆")
            for order in orders[:3]:  # 顯示前3筆
                print(f"  📋 {order.get('symbol')} {order.get('side')} {order.get('executed_quantity')} @ ${order.get('price')} [{order.get('status')}] ({order.get('trading_mode')})")
        else:
            print(f"❌ 訂單歷史失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 訂單歷史錯誤: {e}")    
    print()
    
    # 4. 測試創建一個新的虛擬訂單
    print("🔄 創建虛擬測試訂單...")
    try:
        # 使用 shared_state 中的同一個實例
        from src import shared_state
        paper_client = shared_state.get_paper_trading_client()
        if not paper_client:
            # 如果沒有，就通過 binance_client 取得
            from src.binance_client import binance_client
            paper_client = binance_client.client
        
        order = paper_client.futures_create_order(
            symbol='ADAUSDT',
            side='BUY',
            type='MARKET',
            quantity=10.0
        )
        print(f"✅ 訂單創建成功: {order['symbol']} {order['side']} {order['executedQty']} @ ${order['price']}")
        
        # 再次檢查訂單歷史
        response = requests.get(f"{base_url}/api/orders/history?limit=5")
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ 更新後訂單歷史: {len(orders)} 筆")
            if orders:
                latest_order = orders[-1]
                print(f"  📋 最新: {latest_order.get('symbol')} {latest_order.get('side')} {latest_order.get('executed_quantity')} @ ${latest_order.get('price')}")
        
    except Exception as e:
        print(f"❌ 創建訂單錯誤: {e}")
    
    print()
    print("📋 訂單測試完成！")
    print()
    print("🌐 瀏覽器測試:")
    print(f"  📊 訂單頁面: {base_url}/orders")
    print(f"  📈 Dashboard: {base_url}/")

if __name__ == "__main__":
    test_orders_api()
