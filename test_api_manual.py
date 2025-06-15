#!/usr/bin/env python3
"""
直接通過 API 測試訂單功能
"""
import requests
import json

base_url = "http://localhost:8000"

def test_order_via_api():
    """通過 API 測試訂單功能"""
    print("🧪 通過 API 測試訂單同步功能")
    print("=" * 50)
    
    # 檢查初始狀態
    response = requests.get(f"{base_url}/api/orders/history?limit=5")
    if response.status_code == 200:
        initial_orders = response.json()
        print(f"📋 初始訂單歷史: {len(initial_orders)} 筆")
    
    # 檢查有沒有手動交易的 API
    # 讓我們直接查看 http://localhost:8000/orders 頁面
    print(f"🌐 請打開瀏覽器查看: {base_url}/orders")
    print("   檢查是否有手動創建訂單的功能")
    
    # 也測試一下訂單摘要
    response = requests.get(f"{base_url}/api/orders/summary")
    if response.status_code == 200:
        summary = response.json()
        print(f"📊 訂單摘要: {summary}")
    
    print("\n請在瀏覽器中手動創建一個訂單，然後再次運行測試")

if __name__ == "__main__":
    try:
        test_order_via_api()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
