#!/usr/bin/env python3
"""
測試 Paper Trading 模式的 Discord 通知功能
"""
import asyncio
import time
from src.discord_notifier import DiscordNotifier
from src.config import config

def test_discord_notification():
    """測試 Discord 通知功能"""
    print("🔔 測試 Discord 通知功能...")
    
    notifier = DiscordNotifier()
    
    if not notifier.webhook_url:
        print("❌ Discord webhook URL 未設定")
        return False
    
    # 測試系統通知
    print("📤 發送系統通知...")
    notifier.send_system_notification("🧪 紙上交易系統測試", "系統正常運行，準備開始 paper trading！")
    
    # 測試交易信號通知
    print("📤 發送交易信號通知...")
    notifier.send_signal_notification(
        symbol="BTCUSDT",
        signal="BUY",
        price=45000.0,
        strength=0.75,
        reason="RSI 超賣訊號 (25.3)"
    )
    
    # 測試交易執行通知
    print("📤 發送交易執行通知...")
    notifier.send_trade_notification(
        action="BUY",
        symbol="BTCUSDT",
        quantity=0.1,
        price=45000.0,
        total_value=4500.0,
        fee=4.5,
        trading_mode="paper"
    )
    
    # 測試投資組合通知
    print("📤 發送投資組合通知...")
    notifier.send_portfolio_notification(
        balance=10000.0,
        positions=2,
        daily_pnl=250.0,
        daily_pnl_pct=2.5,
        trading_mode="paper"
    )
    
    print("✅ Discord 通知測試完成")
    return True

def test_paper_trading_functionality():
    """測試 Paper Trading 功能"""
    print("📋 測試 Paper Trading 功能...")
    
    from src.paper_trading_client import paper_trading_client
    
    # 檢查初始餘額
    account = paper_trading_client.get_futures_account()
    print(f"💰 初始餘額: {account['totalWalletBalance']} USDT")
    
    # 測試獲取市場數據
    try:
        ticker = paper_trading_client.get_24hr_ticker("BTCUSDT")
        print(f"📊 BTCUSDT 當前價格: ${ticker.get('lastPrice', ticker.get('price', 'N/A'))}")
    except Exception as e:
        print(f"❌ 獲取市場數據失敗: {e}")
        return False
    
    # 測試虛擬交易
    try:
        print("🔄 執行虛擬買入訂單...")
        order = paper_trading_client.futures_create_order(
            symbol="BTCUSDT",
            side="BUY",
            type="MARKET",
            quantity=0.01
        )
        print(f"✅ 訂單執行成功: {order['symbol']} {order['side']} {order['executedQty']} @ ${order['price']}")
        
        # 檢查持倉
        positions = paper_trading_client.get_futures_positions("BTCUSDT")
        if positions:
            pos = positions[0]
            print(f"📈 持倉更新: {pos['positionAmt']} BTCUSDT @ ${pos['entryPrice']}")
        
    except Exception as e:
        print(f"❌ 虛擬交易執行失敗: {e}")
        return False
    
    print("✅ Paper Trading 功能測試完成")
    return True

def main():
    """主測試函數"""
    print("🚀 開始 Paper Trading 和 Discord 通知測試\n")
    
    # 顯示配置信息
    print(f"📋 當前模式: Paper Trading = {config.binance.paper_trading}")
    print(f"🔗 Discord Webhook: {'已設定' if config.binance.__dict__.get('discord_webhook') else '未設定'}")
    print()
    
    # 測試 Paper Trading 功能
    pt_success = test_paper_trading_functionality()
    print()
    
    # 測試 Discord 通知
    discord_success = test_discord_notification()
    print()
    
    # 總結
    print("📊 測試結果總結:")
    print(f"  📋 Paper Trading: {'✅ 成功' if pt_success else '❌ 失敗'}")
    print(f"  🔔 Discord 通知: {'✅ 成功' if discord_success else '❌ 失敗'}")
    
    if pt_success and discord_success:
        print("\n🎉 所有測試通過！Paper Trading 模式已準備就緒！")
        print("\n📝 使用說明:")
        print("1. 使用真實 Binance API 獲取市場數據")
        print("2. 所有交易都是虛擬的，使用 10,000 USDT 虛擬資金")
        print("3. 策略信號和交易執行會發送到 Discord")
        print("4. 適合測試策略效果和學習交易程式")
    else:
        print("\n⚠️  部分測試失敗，請檢查配置")

if __name__ == "__main__":
    main()
