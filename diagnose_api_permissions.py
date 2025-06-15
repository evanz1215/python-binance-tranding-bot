#!/usr/bin/env python3
"""
詳細的 API 權限診斷工具
"""
import os
import requests
import time
import hmac
import hashlib
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def get_timestamp():
    """獲取當前時間戳"""
    return int(time.time() * 1000)

def create_signature(query_string, secret_key):
    """創建 API 簽名"""
    return hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_api_permissions():
    """測試 API 權限"""
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "")
    
    if not api_key or not secret_key:
        print("❌ API 金鑰未設定")
        return False
    
    # Testnet 基礎 URL
    base_url = "https://testnet.binance.vision"
    
    print(f"🔍 測試 API 權限...")
    print(f"使用 testnet URL: {base_url}")
    print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
    
    # 測試 1: 檢查伺服器時間（不需要簽名）
    print(f"\n1️⃣ 測試伺服器連接...")
    try:
        response = requests.get(f"{base_url}/api/v3/time", timeout=10)
        if response.status_code == 200:
            server_time = response.json()["serverTime"]
            print(f"✅ 伺服器連接成功，伺服器時間: {server_time}")
        else:
            print(f"❌ 伺服器連接失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 伺服器連接錯誤: {e}")
        return False
    
    # 測試 2: 測試 API 金鑰格式（獲取交易所資訊）
    print(f"\n2️⃣ 測試 API 金鑰格式...")
    try:
        headers = {
            "X-MBX-APIKEY": api_key
        }
        response = requests.get(f"{base_url}/api/v3/exchangeInfo", headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ API 金鑰格式正確")
        else:
            print(f"❌ API 金鑰格式錯誤: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ API 金鑰測試錯誤: {e}")
        return False
    
    # 測試 3: 測試帳戶資訊（需要簽名）
    print(f"\n3️⃣ 測試帳戶權限...")
    try:
        timestamp = get_timestamp()
        query_string = f"timestamp={timestamp}"
        signature = create_signature(query_string, secret_key)
        
        headers = {
            "X-MBX-APIKEY": api_key
        }
        
        url = f"{base_url}/api/v3/account?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"✅ 帳戶權限正常")
            print(f"   帳戶類型: {account_data.get('accountType', 'N/A')}")
            
            # 顯示餘額
            balances = [b for b in account_data.get('balances', []) if float(b['free']) > 0 or float(b['locked']) > 0]
            if balances:
                print(f"   非零餘額:")
                for balance in balances[:5]:  # 只顯示前5個
                    total = float(balance['free']) + float(balance['locked'])
                    print(f"     {balance['asset']}: {total:.8f}")
            else:
                print(f"   所有餘額為零")
                
            return True
            
        elif response.status_code == 401:
            error_data = response.json()
            error_code = error_data.get('code', 'N/A')
            error_msg = error_data.get('msg', 'N/A')
            
            print(f"❌ 權限錯誤 (HTTP 401)")
            print(f"   錯誤代碼: {error_code}")
            print(f"   錯誤訊息: {error_msg}")
            
            if error_code == -2015:
                print(f"\n💡 錯誤代碼 -2015 解決建議:")
                print(f"1. 檢查 IP 白名單設定")
                print(f"2. 確認 API 金鑰權限設定")
                print(f"3. 檢查時間同步")
                print(f"4. 重新生成 API 金鑰")
            
            return False
            
        else:
            print(f"❌ 未知錯誤: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 帳戶權限測試錯誤: {e}")
        return False

def check_ip_and_permissions():
    """檢查 IP 和權限建議"""
    print(f"\n🔧 權限檢查建議:")
    print(f"1. 登入 https://testnet.binance.vision/")
    print(f"2. 檢查您的 API 金鑰設定")
    print(f"3. 確認以下權限已啟用:")
    print(f"   ✓ Enable Reading")
    print(f"   ✓ Enable Spot & Margin Trading")
    print(f"4. 檢查 IP 限制設定:")
    print(f"   - 如果設定了 IP 白名單，請確保您的 IP 在列表中")
    print(f"   - 建議先移除 IP 限制進行測試")
    print(f"5. 如果問題持續，請重新生成 API 金鑰")

def main():
    """主要診斷流程"""
    print("🔍 Binance Testnet API 權限詳細診斷")
    print("=" * 60)
    
    success = test_api_permissions()
    
    if not success:
        check_ip_and_permissions()
        print(f"\n❌ API 權限測試失敗")
        return False
    else:
        print(f"\n🎉 所有權限測試通過！")
        return True

if __name__ == "__main__":
    main()
