#!/usr/bin/env python3
"""
API 金鑰驗證工具
用於檢查 Binance testnet API 金鑰是否正確設定
"""
import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def check_env_file():
    """檢查 .env 文件是否存在"""
    if not os.path.exists('.env'):
        print("❌ 錯誤：找不到 .env 文件")
        print("請建立 .env 文件並設定您的 Binance API 金鑰")
        return False
    
    print("✅ 找到 .env 文件")
    return True

def validate_api_keys():
    """驗證 API 金鑰設定"""
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret_key = os.getenv("BINANCE_SECRET_KEY", "")
    testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    
    print(f"\n📋 API 設定檢查:")
    print(f"   Testnet 模式: {testnet}")
    
    # 檢查 API 金鑰
    if not api_key or api_key in ["", "your_testnet_api_key_here", "your_actual_testnet_api_key_here"]:
        print("❌ BINANCE_API_KEY 未設定或仍為預設值")
        return False
    
    if not secret_key or secret_key in ["", "your_testnet_secret_key_here", "your_actual_testnet_secret_key_here"]:
        print("❌ BINANCE_SECRET_KEY 未設定或仍為預設值")
        return False
    
    # 檢查金鑰格式
    if len(api_key) < 60:
        print(f"⚠️  API 金鑰長度可能不正確：{len(api_key)} 字元（期望約 64 字元）")
        return False
        
    if len(secret_key) < 60:
        print(f"⚠️  Secret 金鑰長度可能不正確：{len(secret_key)} 字元（期望約 64 字元）")
        return False
    
    print(f"✅ API 金鑰格式看起來正確")
    print(f"   API Key 長度: {len(api_key)} 字元")
    print(f"   Secret Key 長度: {len(secret_key)} 字元")
    print(f"   API Key 前綴: {api_key[:8]}...")
    
    return True

def test_api_connection():
    """測試 API 連線"""
    try:
        from src.binance_client import BinanceClient
        
        print(f"\n🔌 測試 API 連線...")
        client = BinanceClient()
        
        # 嘗試獲取帳戶資訊
        account_info = client.get_account_info()
        print("✅ API 連線成功！")
        print(f"   帳戶類型: {account_info.get('accountType', 'N/A')}")
        
        # 顯示餘額
        balances = client.get_balance()
        non_zero_balances = {k: v for k, v in balances.items() if v['total'] > 0}
        
        if non_zero_balances:
            print(f"   非零餘額:")
            for asset, balance in non_zero_balances.items():
                print(f"     {asset}: {balance['total']:.8f}")
        else:
            print("   所有餘額為零")
            
        return True
        
    except ImportError as e:
        print(f"❌ 模組導入錯誤: {e}")
        print("請確保已安裝必要的套件：pip install python-binance")
        return False
        
    except Exception as e:
        print(f"❌ API 連線失敗: {e}")
        
        if "API-key format invalid" in str(e):
            print("\n💡 解決建議:")
            print("1. 前往 https://testnet.binance.vision/")
            print("2. 使用 GitHub 帳號登入")
            print("3. 生成新的 API 金鑰")
            print("4. 將新金鑰複製到 .env 文件中")
            print("5. 確保沒有額外的空格或字元")
            
        return False

def main():
    """主要驗證流程"""
    print("🔍 Binance Testnet API 金鑰驗證工具")
    print("=" * 50)
    
    # 檢查 .env 文件
    if not check_env_file():
        sys.exit(1)
    
    # 驗證 API 金鑰
    if not validate_api_keys():
        print("\n💡 如何獲取 Binance Testnet API 金鑰:")
        print("1. 前往 https://testnet.binance.vision/")
        print("2. 使用您的 GitHub 帳號登入")
        print("3. 點擊 'Create a New Key'")
        print("4. 將 API Key 和 Secret Key 複製到 .env 文件中")
        sys.exit(1)
    
    # 測試 API 連線
    if test_api_connection():
        print("\n🎉 所有檢查都通過！您的 API 金鑰設定正確。")
    else:
        print(f"\n❌ API 連線測試失敗。請檢查您的金鑰設定。")
        sys.exit(1)

if __name__ == "__main__":
    main()
