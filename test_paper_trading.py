#!/usr/bin/env python3
"""
紙上交易模式測試和展示
"""
import os

# 設置紙上交易模式
os.environ['PAPER_TRADING'] = 'true'
os.environ['DEMO_MODE'] = 'false'

from src.config import config

def test_paper_trading():
    """測試紙上交易功能"""
    print("📋 PAPER_TRADING=true 功能展示")
    print("=" * 60)
    
    print(f"📊 紙上交易模式: {'✅ 啟用' if config.binance.paper_trading else '❌ 未啟用'}")
    print(f"🎮 Demo 模式: {'✅ 啟用' if config.binance.demo_mode else '❌ 未啟用'}")
    
    if not config.binance.paper_trading:
        print("❌ 紙上交易模式未啟用，請設置 PAPER_TRADING=true")
        return
    
    try:
        from src.paper_trading_client import paper_trading_client
        
        if not paper_trading_client:
            print("❌ 紙上交易客戶端初始化失敗")
            return
        
        print("\n🎯 紙上交易模式特點:")
        print("─" * 50)
        print("✅ 使用真實 Binance API 數據")
        print("✅ 虛擬資金交易 (初始 $10,000)")
        print("✅ 真實市場價格和 K 線數據")
        print("✅ 完整的交易記錄和統計")
        print("✅ 支援 Discord/Telegram 通知")
        print("✅ 零風險策略測試")
        
        print("\n🔧 功能測試:")
        print("─" * 50)
        
        # 1. 測試伺服器時間
        print("1️⃣  伺服器時間同步")
        server_time = paper_trading_client.get_server_time()
        print(f"   ✅ 真實伺服器時間: {server_time['serverTime']}")
        
        # 2. 測試市場數據
        print("\n2️⃣  真實市場數據")
        ticker = paper_trading_client.get_24hr_ticker('BTCUSDT')
        print(f"   ₿ BTC 真實價格: ${float(ticker['lastPrice']):,.2f}")
        print(f"   📈 24h 漲跌幅: {float(ticker['priceChangePercent']):.2f}%")
        print(f"   📊 24h 交易量: {float(ticker['volume']):,.2f}")
        
        # 3. 測試虛擬帳戶
        print("\n3️⃣  虛擬帳戶狀態")
        account = paper_trading_client.get_futures_account()
        print(f"   💰 總錢包餘額: ${float(account['totalWalletBalance']):,.2f}")
        print(f"   💵 可用餘額: ${float(account['availableBalance']):,.2f}")
        
        # 4. 測試 K 線數據
        print("\n4️⃣  真實 K 線數據")
        klines = paper_trading_client.get_klines(symbol='BTCUSDT', interval='1h', limit=3)
        print(f"   📊 獲取了 {len(klines)} 根真實 K 線")
        latest_kline = klines[-1]
        print(f"   📈 最新開盤: ${float(latest_kline[1]):,.2f}")
        print(f"   📉 最新收盤: ${float(latest_kline[4]):,.2f}")
        
        # 5. 測試虛擬交易
        print("\n5️⃣  虛擬交易執行")
        print("   🛒 執行虛擬買入訂單...")
        buy_order = paper_trading_client.futures_create_order(
            symbol='BTCUSDT',
            side='BUY',
            type='MARKET',
            quantity=0.01  # 買入 0.01 BTC
        )
        print(f"   ✅ 訂單執行成功!")
        print(f"   🆔 訂單 ID: {buy_order['orderId']}")
        print(f"   💰 執行數量: {buy_order['executedQty']} BTC")
        print(f"   💵 執行價格: ${float(buy_order['fills'][0]['price']):,.2f}")
        print(f"   💸 手續費: ${float(buy_order['fills'][0]['commission']):.4f}")
        
        # 6. 測試持倉查詢
        print("\n6️⃣  持倉狀態")
        positions = paper_trading_client.get_futures_positions()
        print(f"   📊 當前持倉: {len(positions)} 個")
        for pos in positions:
            print(f"   🎯 {pos['symbol']}: {pos['positionAmt']} @ ${float(pos['entryPrice']):,.2f}")
            print(f"   📈 當前價格: ${float(pos['markPrice']):,.2f}")
            print(f"   💹 未實現盈虧: ${float(pos['unRealizedProfit']):,.4f}")
        
        # 7. 查看交易後的餘額
        print("\n7️⃣  交易後帳戶狀態")
        new_account = paper_trading_client.get_futures_account()
        print(f"   💰 剩餘錢包餘額: ${float(new_account['totalWalletBalance']):,.2f}")
        print(f"   💹 未實現盈虧: ${float(new_account['totalUnrealizedProfit']):,.4f}")
        print(f"   💼 總資產價值: ${float(new_account['totalMarginBalance']):,.2f}")
        
        # 8. 交易統計
        print("\n8️⃣  交易統計")
        stats = paper_trading_client.get_paper_trading_stats()
        print(f"   🏦 初始資金: ${stats['initial_balance']:,.2f}")
        print(f"   💰 當前餘額: ${stats['current_balance']:,.2f}")
        print(f"   💹 未實現盈虧: ${stats['unrealized_pnl']:,.4f}")
        print(f"   📊 總資產價值: ${stats['total_value']:,.2f}")
        print(f"   📈 總盈虧: ${stats['total_pnl']:,.4f} ({stats['pnl_percentage']:+.2f}%)")
        print(f"   🔄 交易筆數: {stats['total_trades']}")
        print(f"   💸 總手續費: ${stats['total_commission']:.4f}")
        
        print("\n🎯 紙上交易 vs Demo 模式對比:")
        print("─" * 50)
        print("| 功能         | Demo 模式    | 紙上交易模式 |")
        print("|--------------|--------------|--------------|")
        print("| 市場數據     | 🎲 模擬生成   | ✅ 真實數據  |")
        print("| 價格波動     | 🎲 隨機模擬   | ✅ 真實波動  |")
        print("| API 連接     | ❌ 無需連接   | ✅ 真實連接  |")
        print("| 策略測試     | ⚠️  不夠真實  | ✅ 高度真實  |")
        print("| 資金風險     | ❌ 零風險     | ❌ 零風險    |")
        print("| 學習效果     | 🎯 基礎學習   | 🎯 專業測試  |")
        
        print("\n💡 建議使用場景:")
        print("─" * 50)
        print("🎮 Demo 模式:")
        print("  - 初學者學習交易概念")
        print("  - 熟悉系統介面和功能")
        print("  - 無需 API 金鑰的快速測試")
        print("")
        print("📋 紙上交易模式:")
        print("  - 策略回測和驗證")
        print("  - 真實市場環境下的風險評估")
        print("  - 系統穩定性測試")
        print("  - 上線前的最後驗證")
        
    except Exception as e:
        print(f"❌ 紙上交易測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_paper_trading()
