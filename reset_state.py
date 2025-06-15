#!/usr/bin/env python3
"""
重設交易引擎狀態的腳本
"""
import requests

def reset_trading_state():
    """重設交易引擎狀態"""
    try:
        # 停止交易（如果正在運行）
        response = requests.post("http://localhost:8000/api/trading/stop")
        print(f"停止交易: {response.status_code}")
        
        # 檢查狀態
        response = requests.get("http://localhost:8000/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"交易狀態: {status}")
        else:
            print(f"狀態檢查失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    reset_trading_state()
