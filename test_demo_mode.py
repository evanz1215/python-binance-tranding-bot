#!/usr/bin/env python3
"""
Demo 模式功能測試和展示
"""
import os
import sys

# 暫時設置 DEMO_MODE 為 true
os.environ['DEMO_MODE'] = 'true'

from src.config import config
from src.demo_client import demo_client

def demo_functionality_showcase():
    """展示 Demo 模式的功能"""
    print("🎮 DEMO_MODE=true 功能展示")
    print("=" * 60)
    
    print(f"📋 Demo 模式狀態: {'✅ 啟用' if config.binance.demo_mode else '❌ 未啟用'}")
    
    if not config.binance.demo_mode:
        print("❌ Demo 模式未啟用，請設置 DEMO_MODE=true")
        return
    
    print("\n🔧 Demo 模式提供的功能:")
    print("─" * 40)
    
    # 1. 模擬伺服器時間
    print("1️⃣  模擬伺服器時間同步")
    server_time = demo_client.get_server_time()
    print(f"   📅 模擬伺服器時間: {server_time['serverTime']}")
    
    # 2. 模擬帳戶資訊
    print("\n2️⃣  模擬帳戶資訊")
    account = demo_client.get_account_info()
    print(f"   💰 帳戶可交易: {account['canTrade']}")
    print(f"   💳 餘額數量: {len(account['balances'])} 種資產")
    
    # 3. 模擬餘額查詢
    print("\n3️⃣  模擬餘額查詢")
    balance = demo_client.get_balance('USDT')
    print(f"   💵 USDT 可用餘額: {balance['free']}")
    print(f"   💼 USDT 總餘額: {balance['total']}")
    
    # 4. 模擬合約帳戶
    print("\n4️⃣  模擬合約帳戶")
    futures_account = demo_client.get_futures_account()
    print(f"   🏦 總錢包餘額: {futures_account['totalWalletBalance']}")
    print(f"   📊 可用餘額: {futures_account['availableBalance']}")
    
    # 5. 模擬價格數據
    print("\n5️⃣  模擬市場數據")
    ticker = demo_client.get_24hr_ticker('BTCUSDT')
    print(f"   ₿ BTC 當前價格: ${float(ticker['lastPrice']):,.2f}")
    print(f"   📈 24h 漲跌幅: {float(ticker['priceChangePercent']):.2f}%")
    
    # 6. 模擬 K 線數據
    print("\n6️⃣  模擬 K 線數據")
    klines = demo_client.get_klines(symbol='BTCUSDT', interval='1h', limit=5)
    print(f"   📊 獲取了 {len(klines)} 根 K 線")
    print(f"   📈 最新開盤價: ${float(klines[-1][1]):,.2f}")
    print(f"   📉 最新收盤價: ${float(klines[-1][4]):,.2f}")
    
    # 7. 模擬訂單創建
    print("\n7️⃣  模擬交易訂單")
    print("   🛒 模擬買入訂單...")
    buy_order = demo_client.futures_create_order(
        symbol='BTCUSDT',
        side='BUY',
        type='MARKET',
        quantity=0.001
    )
    print(f"   ✅ 訂單 ID: {buy_order['orderId']}")
    print(f"   💰 執行數量: {buy_order['executedQty']} BTC")
    print(f"   💵 執行價格: ${float(buy_order['fills'][0]['price']):,.2f}")
    
    # 8. 模擬持倉查詢
    print("\n8️⃣  模擬持倉查詢")
    positions = demo_client.get_futures_positions()
    print(f"   📊 當前持倉數量: {len(positions)}")
    if positions:
        for pos in positions:
            print(f"   🎯 {pos['symbol']}: {pos['positionAmt']} @ ${float(pos['entryPrice']):,.2f}")
    
    # 9. 查看更新後的餘額
    print("\n9️⃣  交易後餘額變化")
    new_balance = demo_client.get_balance('USDT')
    print(f"   💵 交易後 USDT 餘額: {new_balance['free']:.2f}")
    print(f"   📉 餘額變化: {new_balance['free'] - balance['free']:.2f}")
    
    print("\n🎯 Demo 模式特點:")
    print("─" * 40)
    print("✅ 無需真實 API 金鑰")
    print("✅ 所有交易都是模擬的")
    print("✅ 適合學習和測試")
    print("✅ 支援所有交易功能")
    print("✅ 實時價格模擬")
    print("✅ 餘額和持倉追蹤")
    print("✅ 安全無風險")
    
    print("\n💡 使用方式:")
    print("─" * 40)
    print("1. 在 .env 檔案中設置 DEMO_MODE=true")
    print("2. 重新啟動交易機器人")
    print("3. 所有功能都會使用模擬數據")
    print("4. 可以安全地測試策略和功能")

if __name__ == "__main__":
    demo_functionality_showcase()
