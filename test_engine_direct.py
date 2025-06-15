#!/usr/bin/env python3
"""
直接測試交易引擎啟動
"""
import asyncio
import sys
from src.trading_engine import TradingEngine

async def test_engine_start():
    """測試交易引擎直接啟動"""
    print("🧪 直接測試交易引擎啟動...")
    
    try:
        print("1. 創建交易引擎...")
        engine = TradingEngine("ma_cross")
        print(f"   ✅ 交易引擎創建成功")
        print(f"   初始 is_running 狀態: {engine.is_running}")
        
        print("2. 啟動交易引擎...")
        await engine.start()
        print(f"   啟動完成，is_running 狀態: {engine.is_running}")
        
        if engine.is_running:
            print("   ✅ 交易引擎啟動成功！")
            
            # 測試停止
            print("3. 停止交易引擎...")
            await engine.stop()
            print(f"   停止完成，is_running 狀態: {engine.is_running}")
        else:
            print("   ❌ 交易引擎啟動失敗")
            
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_engine_start())
