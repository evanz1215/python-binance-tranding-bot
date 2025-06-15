#!/usr/bin/env python3
"""
Simplified system test for the Binance Trading Bot
"""
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")


def print_status(item: str, status: str, details: str = ""):
    """Print a status line"""
    status_emoji = "✅" if status == "OK" else "❌" if status == "FAILED" else "⚠️"
    print(f"{status_emoji} {item}: {status}")
    if details:
        print(f"   └─ {details}")


def check_file_structure():
    """Check if all required files exist"""
    print_header("FILE STRUCTURE CHECK")
    
    required_files = [
        "main.py",
        "demo.py",
        "setup.py",
        "monitor.py",
        "README.md",
        "QUICKSTART.md",
        ".env.example",
        "pyproject.toml",
        "src/__init__.py",
        "src/config.py",
        "src/binance_client.py",
        "src/data_manager.py",
        "src/risk_manager.py",
        "src/trading_engine.py",
        "src/backtest_engine.py",
        "src/notifications.py",
        "src/api.py",
        "src/database/__init__.py",
        "src/database/models.py",
        "src/strategies/__init__.py",
        "src/strategies/base.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print_status(file_path, "OK")
        else:
            print_status(file_path, "MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0


def test_imports():
    """Test module imports"""
    print_header("MODULE IMPORT TEST")
    
    modules = [
        ("config", "src.config"),
        ("strategies", "src.strategies"),
        ("binance_client", "src.binance_client"),
        ("data_manager", "src.data_manager"),
        ("risk_manager", "src.risk_manager"),
        ("trading_engine", "src.trading_engine"),
        ("backtest_engine", "src.backtest_engine"),
        ("notifications", "src.notifications"),
        ("api", "src.api"),
        ("database.models", "src.database.models"),
    ]
    
    success_count = 0
    for module_name, module_path in modules:
        try:
            __import__(module_path)
            print_status(f"Module {module_name}", "OK")
            success_count += 1
        except Exception as e:
            print_status(f"Module {module_name}", "FAILED", str(e))
    
    return success_count == len(modules)


def test_configuration():
    """Test configuration"""
    print_header("CONFIGURATION TEST")
    
    try:
        from src.config import config
        print_status("Configuration Import", "OK")
        
        # Test configuration values
        print_status("Base Currency", "OK", config.trading.base_currency)
        print_status("Max Positions", "OK", str(config.trading.max_positions))
        print_status("Position Size", "OK", f"{config.trading.position_size_pct * 100}%")
        print_status("Stop Loss", "OK", f"{config.trading.stop_loss_pct * 100}%")
        print_status("Take Profit", "OK", f"{config.trading.take_profit_pct * 100}%")
        print_status("Testnet Mode", "OK", str(config.is_testnet))
        
        return True
    except Exception as e:
        print_status("Configuration", "FAILED", str(e))
        return False


def test_strategies():
    """Test strategy imports"""
    print_header("STRATEGY TEST")
    
    try:
        from src.strategies import STRATEGIES, get_strategy
        print_status("Strategy Module Import", "OK", f"{len(STRATEGIES)} strategies found")
        
        success_count = 0
        for strategy_name in STRATEGIES:
            try:
                strategy = get_strategy(strategy_name)
                print_status(f"Strategy {strategy_name}", "OK")
                success_count += 1
            except Exception as e:
                print_status(f"Strategy {strategy_name}", "FAILED", str(e))
        
        return success_count == len(STRATEGIES)
    except Exception as e:
        print_status("Strategy Import", "FAILED", str(e))
        return False


def display_usage_examples():
    """Display usage examples"""
    print_header("USAGE EXAMPLES")
    
    examples = [
        ("Run Demo", "python demo.py"),
        ("Start Web Interface", "python main.py api"),
        ("Update Market Data", "python main.py update-data --symbols BTCUSDT"),
        ("Run Backtest", "python main.py backtest --strategy ma_cross --symbols BTCUSDT --days 7"),
        ("Test Notifications", "python main.py test-notifications"),
        ("System Test", "python system_test.py"),
    ]
    
    for description, command in examples:
        print(f"📌 {description}:")
        print(f"   {command}")
        print()


def main():
    """Run system test"""
    print_header("BINANCE TRADING BOT - SYSTEM TEST")
    
    start_time = time.time()
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if check_file_structure():
        tests_passed += 1
    
    if test_imports():
        tests_passed += 1
    
    if test_configuration():
        tests_passed += 1
    
    if test_strategies():
        tests_passed += 1
    
    # Display usage examples
    display_usage_examples()
    
    # Test summary
    end_time = time.time()
    print_header("TEST SUMMARY")
    print(f"📊 Tests passed: {tests_passed}/{total_tests}")
    print(f"⏱️  Test time: {end_time - start_time:.2f} seconds")
    print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if tests_passed == total_tests:
        print("\n✅ All tests passed! The system is ready to use.")
        print("\n🚀 Next Steps:")
        print("1. Configure .env file with your API keys")
        print("2. Run: python demo.py (to see features)")
        print("3. Run: python main.py update-data --symbols BTCUSDT")
        print("4. Test: python main.py backtest --strategy ma_cross --symbols BTCUSDT --days 7")
        print("5. Start: python main.py api (web interface)")
    else:
        print(f"\n❌ {total_tests - tests_passed} tests failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    main()
