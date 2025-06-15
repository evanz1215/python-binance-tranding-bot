#!/usr/bin/env python3
"""
Simple monitoring script for the trading bot
"""
import asyncio
import time
from datetime import datetime
import json
import requests
from typing import Dict, Any


class BotMonitor:
    """Simple bot monitoring class"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.last_status = None
        
    async def check_status(self) -> Dict[str, Any]:
        """Check bot status via API"""
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection failed: {e}"}
    
    async def check_risk(self) -> Dict[str, Any]:
        """Check risk report"""
        try:
            response = requests.get(f"{self.api_url}/api/risk/report", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Connection failed: {e}"}
    
    def format_status(self, status: Dict[str, Any]) -> str:
        """Format status for display"""
        if "error" in status:
            return f"❌ ERROR: {status['error']}"
        
        is_running = status.get('is_running', False)
        status_icon = "🟢" if is_running else "🔴"
        
        risk_level = status.get('risk_level', 'UNKNOWN')
        risk_icons = {
            'LOW': '🟢',
            'MEDIUM': '🟡', 
            'HIGH': '🟠',
            'CRITICAL': '🔴'
        }
        risk_icon = risk_icons.get(risk_level, '❓')
        
        daily_pnl = status.get('daily_pnl', 0)
        pnl_icon = "📈" if daily_pnl >= 0 else "📉"
        
        return (
            f"{status_icon} Bot: {'RUNNING' if is_running else 'STOPPED'} | "
            f"{risk_icon} Risk: {risk_level} | "
            f"💰 Balance: ${status.get('total_balance', 0):.2f} | "
            f"{pnl_icon} P&L: ${daily_pnl:.2f} | "
            f"📊 Positions: {status.get('active_positions', 0)}"
        )
    
    async def monitor_loop(self, interval: int = 60):
        """Main monitoring loop"""
        print("🤖 Starting Bot Monitor")
        print("=" * 50)
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Check status
                status = await self.check_status()
                status_str = self.format_status(status)
                
                print(f"[{timestamp}] {status_str}")
                
                # Check for alerts
                if not status.get("error"):
                    await self.check_alerts(status)
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(interval)
    
    async def check_alerts(self, status: Dict[str, Any]):
        """Check for alert conditions"""
        # Check if status changed
        if self.last_status:
            if (self.last_status.get('is_running') and 
                not status.get('is_running')):
                print("🚨 ALERT: Bot has stopped!")
            
            if (status.get('risk_level') == 'CRITICAL' and 
                self.last_status.get('risk_level') != 'CRITICAL'):
                print("🚨 CRITICAL RISK ALERT!")
            
            # Check for significant balance change
            last_balance = self.last_status.get('total_balance', 0)
            current_balance = status.get('total_balance', 0)
            if last_balance > 0:
                change_pct = (current_balance - last_balance) / last_balance
                if abs(change_pct) > 0.05:  # 5% change
                    direction = "📈 UP" if change_pct > 0 else "📉 DOWN"
                    print(f"💰 BALANCE ALERT: {direction} {change_pct:.1%}")
        
        self.last_status = status
    
    def print_summary(self):
        """Print monitoring summary"""
        if self.last_status and not self.last_status.get("error"):
            print("\n" + "=" * 50)
            print("📊 CURRENT STATUS SUMMARY")
            print("=" * 50)
            
            status = self.last_status
            print(f"Status: {'RUNNING' if status.get('is_running') else 'STOPPED'}")
            print(f"Strategy: {status.get('strategy', 'N/A')}")
            print(f"Risk Level: {status.get('risk_level', 'UNKNOWN')}")
            print(f"Balance: ${status.get('total_balance', 0):.2f}")
            print(f"Daily P&L: ${status.get('daily_pnl', 0):.2f}")
            print(f"Active Positions: {status.get('active_positions', 0)}")
            print(f"Monitored Symbols: {status.get('monitored_symbols', 0)}")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot Monitor")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="API URL")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Check interval in seconds")
    
    args = parser.parse_args()
    
    monitor = BotMonitor(args.url)
    
    try:
        await monitor.monitor_loop(args.interval)
    finally:
        monitor.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
