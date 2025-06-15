#!/usr/bin/env python3
"""
Quick setup script for the Binance Trading Bot
"""
import os
import sys
import shutil
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data", 
        "backtest_results",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_environment():
    """Setup environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys!")
    elif env_file.exists():
        print("ℹ️  .env file already exists")
    else:
        print("❌ .env.example not found")


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        sys.exit(1)
    else:
        print(f"✅ Python version: {sys.version}")


def install_dependencies():
    """Install dependencies"""
    try:
        import subprocess
        print("📦 Installing dependencies...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")


def main():
    """Main setup function"""
    print("🤖 Binance Trading Bot Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Install dependencies
    install_dependencies()
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your Binance API keys")
    print("2. Run: python main.py update-data")
    print("3. Run a backtest: python main.py backtest --strategy ma_cross")
    print("4. Start trading: python main.py trade --strategy ma_cross")
    print("5. Or start web interface: python main.py api")


if __name__ == "__main__":
    main()
