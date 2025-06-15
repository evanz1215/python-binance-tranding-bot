#!/usr/bin/env python3
"""
Binance API Key Diagnostic Tool
檢查和診斷 Binance API 金鑰的權限和設定
"""

import asyncio
import sys
from typing import Dict, Any

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from src.config import config
from src.binance_client import BinanceClient, get_client


class APIKeyDiagnostic:
    """API 金鑰診斷工具"""
    
    def __init__(self):
        self.results = {}
    
    def check_environment_config(self) -> Dict[str, Any]:
        """檢查環境變數配置"""
        logger.info("🔍 檢查環境變數配置...")
        
        config_status = {
            "testnet_mode": config.binance.testnet,
            "demo_mode": config.binance.demo_mode,
            "trading_mode": config.binance.trading_mode,
            "spot_credentials": {
                "api_key_set": bool(config.binance.spot_api_key),
                "secret_key_set": bool(config.binance.spot_secret_key),
                "api_key_length": len(config.binance.spot_api_key) if config.binance.spot_api_key else 0,
                "secret_key_length": len(config.binance.spot_secret_key) if config.binance.spot_secret_key else 0
            },
            "futures_credentials": {
                "api_key_set": bool(config.binance.futures_api_key),
                "secret_key_set": bool(config.binance.futures_secret_key),
                "api_key_length": len(config.binance.futures_api_key) if config.binance.futures_api_key else 0,
                "secret_key_length": len(config.binance.futures_secret_key) if config.binance.futures_secret_key else 0
            }
        }
        
        # 打印配置狀態
        print("\n📋 配置狀態:")
        print(f"  Testnet 模式: {'✅' if config_status['testnet_mode'] else '❌'}")
        print(f"  Demo 模式: {'✅' if config_status['demo_mode'] else '❌'}")
        print(f"  交易模式: {config_status['trading_mode']}")
        
        print(f"\n🔑 現貨 API 憑證:")
        print(f"  API Key: {'✅' if config_status['spot_credentials']['api_key_set'] else '❌'} ({config_status['spot_credentials']['api_key_length']} 字符)")
        print(f"  Secret Key: {'✅' if config_status['spot_credentials']['secret_key_set'] else '❌'} ({config_status['spot_credentials']['secret_key_length']} 字符)")
        
        print(f"\n🚀 合約 API 憑證:")
        print(f"  API Key: {'✅' if config_status['futures_credentials']['api_key_set'] else '❌'} ({config_status['futures_credentials']['api_key_length']} 字符)")
        print(f"  Secret Key: {'✅' if config_status['futures_credentials']['secret_key_set'] else '❌'} ({config_status['futures_credentials']['secret_key_length']} 字符)")
        
        return config_status
    
    async def test_spot_api(self) -> Dict[str, Any]:
        """測試現貨 API"""
        logger.info("🔍 測試現貨 API...")
        
        if not config.binance.has_valid_credentials("spot"):
            return {"status": "skipped", "reason": "No spot API credentials"}
        
        try:
            client = BinanceClient("spot")
            
            tests = {}
            
            # 測試 1: 獲取服務器時間
            try:
                server_time = client.client.get_server_time()
                tests["server_time"] = {"status": "success", "data": server_time}
                print("  ✅ 服務器時間: 成功")
            except Exception as e:
                tests["server_time"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 服務器時間: {e}")
            
            # 測試 2: 獲取賬戶信息
            try:
                account_info = client.get_account_info()
                tests["account_info"] = {"status": "success", "data": {"canTrade": account_info.get("canTrade")}}
                print("  ✅ 賬戶信息: 成功")
            except Exception as e:
                tests["account_info"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 賬戶信息: {e}")
              # 測試 3: 獲取餘額
            try:
                account_info = client.get_account_info()
                balances = account_info.get('balances', [])
                tests["balances"] = {"status": "success", "count": len([b for b in balances if float(b.get('free', 0)) > 0])}
                print(f"  ✅ 餘額信息: 成功 ({len(balances)} 個資產)")
            except Exception as e:
                tests["balances"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 餘額信息: {e}")
            
            return {"status": "completed", "tests": tests}
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def test_futures_api(self) -> Dict[str, Any]:
        """測試合約 API"""
        logger.info("🔍 測試合約 API...")
        
        if not config.binance.has_valid_credentials("futures"):
            return {"status": "skipped", "reason": "No futures API credentials"}
        
        try:
            client = BinanceClient("futures")
            
            tests = {}
            
            # 測試 1: 獲取服務器時間
            try:
                server_time = client.client.get_server_time()
                tests["server_time"] = {"status": "success", "data": server_time}
                print("  ✅ 服務器時間: 成功")
            except Exception as e:
                tests["server_time"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 服務器時間: {e}")
            
            # 測試 2: 獲取合約賬戶信息
            try:
                account_info = client.get_futures_account()
                tests["futures_account"] = {"status": "success", "data": {"canTrade": account_info.get("canTrade")}}
                print("  ✅ 合約賬戶: 成功")
            except Exception as e:
                tests["futures_account"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 合約賬戶: {e}")
            
            # 測試 3: 獲取持倉
            try:
                positions = client.get_futures_positions()
                tests["positions"] = {"status": "success", "count": len([p for p in positions if float(p.get('positionAmt', 0)) != 0])}
                print(f"  ✅ 持倉信息: 成功")
            except Exception as e:
                tests["positions"] = {"status": "failed", "error": str(e)}
                print(f"  ❌ 持倉信息: {e}")
            
            return {"status": "completed", "tests": tests}
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def run_full_diagnostic(self):
        """運行完整診斷"""
        print("🔧 Binance API 金鑰診斷工具")
        print("=" * 50)
        
        # 檢查配置
        self.results["config"] = self.check_environment_config()
        
        # 測試現貨 API
        print(f"\n🏪 測試現貨 API:")
        self.results["spot"] = await self.test_spot_api()
        
        # 測試合約 API
        print(f"\n🚀 測試合約 API:")
        self.results["futures"] = await self.test_futures_api()
        
        # 總結
        print(f"\n📊 診斷總結:")
        print("=" * 30)
        
        if self.results["spot"]["status"] == "completed":
            spot_success = sum(1 for test in self.results["spot"]["tests"].values() if test["status"] == "success")
            spot_total = len(self.results["spot"]["tests"])
            print(f"現貨 API: {spot_success}/{spot_total} 測試通過")
        else:
            print(f"現貨 API: {self.results['spot']['status']}")
            
        if self.results["futures"]["status"] == "completed":
            futures_success = sum(1 for test in self.results["futures"]["tests"].values() if test["status"] == "success")
            futures_total = len(self.results["futures"]["tests"])
            print(f"合約 API: {futures_success}/{futures_total} 測試通過")
        else:
            print(f"合約 API: {self.results['futures']['status']}")
        
        # 建議
        print(f"\n💡 建議:")
        self.print_suggestions()
    
    def print_suggestions(self):
        """打印建議"""
        suggestions = []
        
        # 檢查配置問題
        if not config.binance.has_valid_credentials("spot") and not config.binance.has_valid_credentials("futures"):
            suggestions.append("❗ 沒有配置任何有效的 API 憑證，請檢查 .env 檔案")
        
        if config.binance.testnet:
            suggestions.append("🧪 您正在使用 testnet 模式，請確認使用的是 testnet API 金鑰")
        
        # 檢查測試結果
        if self.results.get("futures", {}).get("status") == "completed":
            futures_tests = self.results["futures"]["tests"]
            if futures_tests.get("futures_account", {}).get("status") == "failed":
                error = futures_tests["futures_account"].get("error", "")
                if "APIError(code=-2015)" in error:
                    suggestions.append("🔑 合約 API 金鑰權限不足，請在 Binance 中啟用期貨交易權限")
                if "APIError(code=-1021)" in error:
                    suggestions.append("⏰ 時間戳錯誤，請檢查系統時間是否同步")
        
        if not suggestions:
            suggestions.append("✅ 配置看起來正常！")
        
        for suggestion in suggestions:
            print(f"  {suggestion}")


async def main():
    """主函數"""
    diagnostic = APIKeyDiagnostic()
    await diagnostic.run_full_diagnostic()


if __name__ == "__main__":
    asyncio.run(main())
