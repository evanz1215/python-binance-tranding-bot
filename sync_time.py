#!/usr/bin/env python3
"""
系統時間同步工具
"""
import subprocess
import time
from datetime import datetime

def sync_system_time():
    """同步系統時間"""
    print("🕐 開始同步系統時間...")
    
    try:
        # Windows 時間同步指令
        result = subprocess.run(
            ["w32tm", "/resync"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ 系統時間同步成功")
            print(f"📅 當前系統時間: {datetime.now()}")
            return True
        else:
            print(f"❌ 系統時間同步失敗: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 時間同步超時")
        return False
    except Exception as e:
        print(f"❌ 時間同步錯誤: {e}")
        return False

def check_time_service():
    """檢查 Windows 時間服務"""
    print("🔍 檢查 Windows 時間服務狀態...")
    
    try:
        result = subprocess.run(
            ["sc", "query", "w32time"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "RUNNING" in result.stdout:
            print("✅ Windows 時間服務正在運行")
            return True
        else:
            print("⚠️  Windows 時間服務未運行")
            print("💡 嘗試啟動時間服務...")
            
            start_result = subprocess.run(
                ["net", "start", "w32time"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if start_result.returncode == 0:
                print("✅ Windows 時間服務已啟動")
                return True
            else:
                print(f"❌ 無法啟動時間服務: {start_result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ 檢查時間服務錯誤: {e}")
        return False

def main():
    """主函數"""
    print("⏰ Binance API 時間同步工具")
    print("=" * 50)
    
    # 檢查時間服務
    if check_time_service():
        # 同步系統時間
        if sync_system_time():
            print("\n🎉 時間同步完成！")
            print("💡 請重新啟動 API 服務器以應用變更")
        else:
            print("\n❌ 時間同步失敗")
            print("💡 請手動檢查系統時間設定")
    else:
        print("\n❌ 時間服務問題")
        print("💡 請以管理員身份運行此腳本")

if __name__ == "__main__":
    main()
