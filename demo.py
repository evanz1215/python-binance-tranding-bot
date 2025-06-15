#!/usr/bin/env python3
"""
Demo script to showcase the Binance Trading Bot features
"""
import asyncio
import sys
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append('src')

from src.config import config
from src.strategies import get_strategy
from src.backtest_engine import backtest_engine


async def demo_strategy_analysis():
    """Demo strategy analysis with sample data"""
    print("🔍 策略分析演示")
    print("=" * 50)
    
    # Create sample OHLCV data (simulated)
    import pandas as pd
    import numpy as np
    
    # Generate sample price data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    prices = 50000 + np.cumsum(np.random.randn(100) * 100)  # Starting from $50,000
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(100) * 50,
        'high': prices + np.abs(np.random.randn(100) * 100),
        'low': prices - np.abs(np.random.randn(100) * 100),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 100)
    }).set_index('timestamp')
    
    # Test different strategies
    strategies = ['ma_cross', 'rsi', 'macd', 'bollinger_bands']
    
    for strategy_name in strategies:
        print(f"\n📊 測試策略: {strategy_name}")
        try:
            strategy = get_strategy(strategy_name)
            signal = strategy.analyze("BTCUSDT", sample_data)
            print(f"   信號: {signal.action}")
            print(f"   強度: {signal.strength:.2f}")
            print(f"   原因: {signal.reason}")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")


def demo_configuration():
    """Demo configuration system"""
    print("\n⚙️ 配置系統演示")
    print("=" * 50)
    
    print(f"📈 基礎貨幣: {config.trading.base_currency}")
    print(f"💰 倉位大小: {config.trading.position_size_pct:.1%}")
    print(f"🛑 停損比例: {config.trading.stop_loss_pct:.1%}")
    print(f"🎯 止盈比例: {config.trading.take_profit_pct:.1%}")
    print(f"📊 最大倉位數: {config.trading.max_positions}")
    print(f"⚠️ 每日最大虧損: {config.trading.max_daily_loss_pct:.1%}")
    print(f"📉 最大回撤: {config.trading.max_drawdown_pct:.1%}")


async def demo_backtest():
    """Demo backtesting with simulated data"""
    print("\n📈 回測演示")
    print("=" * 50)
    
    try:
        # Note: This would need real market data in actual use
        print("⚠️ 注意: 回測需要真實市場數據")
        print("📊 要運行真實回測，請使用:")
        print("   python main.py backtest --strategy ma_cross --symbols BTCUSDT ETHUSDT")
        
        # Show what a backtest result might look like
        print("\n📊 模擬回測結果範例:")
        print("   策略: 移動平均交叉")
        print("   期間: 30天")
        print("   初始資金: $10,000")
        print("   最終資金: $11,250")
        print("   總回報: $1,250 (12.5%)")
        print("   最大回撤: 5.8%")
        print("   夏普比率: 1.85")
        print("   總交易次數: 45")
        print("   勝率: 62.2%")
        
    except Exception as e:
        print(f"❌ 回測演示錯誤: {e}")


def demo_risk_management():
    """Demo risk management features"""
    print("\n⚠️ 風險管理演示")
    print("=" * 50)
    
    print("🛡️ 風險管理功能:")
    print("   ✅ 自動停損和止盈")
    print("   ✅ 倉位大小控制")
    print("   ✅ 每日虧損限制")
    print("   ✅ 最大回撤保護")
    print("   ✅ 風險等級評估")
    print("   ✅ 實時風險監控")
    
    print("\n📊 風險等級:")
    print("   🟢 低風險: 正常交易")
    print("   🟡 中等風險: 謹慎交易")
    print("   🟠 高風險: 限制交易")
    print("   🔴 極高風險: 停止交易")


def demo_features():
    """Demo all bot features"""
    print("🤖 Binance 自動交易機器人功能演示")
    print("=" * 60)
    
    # Configuration demo
    demo_configuration()
    
    # Risk management demo
    demo_risk_management()
    
    print("\n📱 可用功能:")
    print("=" * 50)
    print("🎯 交易策略:")
    print("   • 移動平均交叉 (MA Cross)")
    print("   • RSI 策略")
    print("   • MACD 策略") 
    print("   • 布林帶策略")
    print("   • 組合策略")
    
    print("\n📊 數據管理:")
    print("   • 實時市場數據收集")
    print("   • 多時間框架支援")
    print("   • 歷史數據存儲")
    print("   • 自動數據更新")
    
    print("\n🔔 通知系統:")
    print("   • Telegram 通知")
    print("   • Discord 通知")
    print("   • 交易執行提醒")
    print("   • 風險警報")
    
    print("\n🌐 Web 介面:")
    print("   • 實時監控儀表板")
    print("   • 交易控制面板")
    print("   • 風險管理報告")
    print("   • 回測結果查看")
    
    print("\n📋 可用命令:")
    print("=" * 50)
    print("🚀 開始交易:")
    print("   python main.py trade --strategy ma_cross")
    
    print("\n📈 運行回測:")
    print("   python main.py backtest --strategy ma_cross --days 30")
    
    print("\n🌐 啟動 Web 介面:")
    print("   python main.py api")
    
    print("\n📊 更新數據:")
    print("   python main.py update-data")
    
    print("\n🔔 測試通知:")
    print("   python main.py test-notifications")


async def main():
    """Main demo function"""
    try:
        # Show features overview
        demo_features()
        
        # Demo strategy analysis
        await demo_strategy_analysis()
        
        # Demo backtest
        await demo_backtest()
        
        print("\n" + "=" * 60)
        print("✨ 演示完成!")
        print("📖 查看 README.md 獲取完整說明")
        print("🚀 查看 QUICKSTART.md 獲取快速入門指南")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 演示錯誤: {e}")


if __name__ == "__main__":
    asyncio.run(main())
