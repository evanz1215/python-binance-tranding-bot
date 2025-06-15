#!/usr/bin/env python3
"""
測試 Binance API 時間同步
"""
import time
from datetime import datetime
from src.binance_client import binance_client

def test_time_sync():
    """測試時間同步"""
    print("🕐 測試 Binance API 時間同步...")
    
    try:
        # 獲取本地時間
        local_time = int(time.time() * 1000)
        local_datetime = datetime.fromtimestamp(local_time / 1000)
        
        print(f"📅 本地時間: {local_datetime} ({local_time})")
        
        # 獲取伺服器時間
        server_time_resp = binance_client.client.get_server_time()
        server_time = server_time_resp['serverTime']
        server_datetime = datetime.fromtimestamp(server_time / 1000)
        
        print(f"🌐 伺服器時間: {server_datetime} ({server_time})")
        
        # 計算時間差
        time_diff = server_time - local_time
        print(f"⏰ 時間差: {time_diff}ms")
        
        if abs(time_diff) > 1000:
            print("❌ 時間差超過 1000ms，可能會導致 API 錯誤")
            print("💡 建議同步系統時間或調整時區設定")
        elif abs(time_diff) > 500:
            print("⚠️  時間差超過 500ms，建議注意")
        else:
            print("✅ 時間同步正常")
            
        # 測試簡單的 API 呼叫
        print("\n🔍 測試 API 呼叫...")
        account = binance_client.get_futures_account()
        print("✅ API 呼叫成功，時間同步正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 時間同步測試失敗: {e}")
        return False

if __name__ == "__main__":
    test_time_sync()
