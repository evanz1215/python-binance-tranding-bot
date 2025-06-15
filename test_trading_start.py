#!/usr/bin/env python3
"""
測試交易啟動功能
"""
import asyncio
import aiohttp
import json

async def test_trading_start():
    """測試交易啟動"""
    print("🧪 測試交易啟動功能...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 1. 檢查初始狀態
        print("\n1. 檢查初始狀態...")
        async with session.get(f"{base_url}/api/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"   初始狀態: {'運行中' if status['is_running'] else '已停止'}")
                print(f"   策略: {status['strategy']}")
            else:
                print(f"   ❌ 狀態檢查失敗: {resp.status}")
                return
        
        # 2. 啟動交易
        print("\n2. 啟動交易...")
        async with session.post(f"{base_url}/api/trading/start") as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ 啟動請求成功: {result['message']}")
                if 'engine_status' in result:
                    print(f"   引擎狀態: {result['engine_status']}")
            else:
                error = await resp.text()
                print(f"   ❌ 啟動失敗: {resp.status} - {error}")
                return
        
        # 3. 等待一下然後檢查狀態
        print("\n3. 等待並檢查狀態...")
        await asyncio.sleep(2)
        
        async with session.get(f"{base_url}/api/status") as resp:
            if resp.status == 200:
                status = await resp.json()
                print(f"   當前狀態: {'✅ 運行中' if status['is_running'] else '❌ 已停止'}")
                print(f"   策略: {status['strategy']}")
                print(f"   會話ID: {status.get('session_id', 'None')}")
                print(f"   監控符號數: {status['monitored_symbols']}")
                print(f"   活躍持倉: {status['active_positions']}")
            else:
                print(f"   ❌ 狀態檢查失敗: {resp.status}")
        
        # 4. 如果成功啟動，再測試停止
        if status.get('is_running'):
            print("\n4. 測試停止交易...")
            async with session.post(f"{base_url}/api/trading/stop") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"   ✅ 停止請求成功: {result['message']}")
                else:
                    error = await resp.text()
                    print(f"   ❌ 停止失敗: {resp.status} - {error}")
            
            # 最終狀態檢查
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/api/status") as resp:
                if resp.status == 200:
                    final_status = await resp.json()
                    print(f"   最終狀態: {'運行中' if final_status['is_running'] else '✅ 已停止'}")

if __name__ == "__main__":
    asyncio.run(test_trading_start())
