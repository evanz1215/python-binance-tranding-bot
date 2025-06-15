#!/usr/bin/env python3
"""
Discord 通知器 - 支援 Demo 和紙上交易模式
"""
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from .config import config


class DiscordNotifier:
    """Discord 通知器"""
    
    def __init__(self):
        # 從配置讀取 webhook URL（支援兩種配置名稱）
        self.webhook_url = (
            config.binance.__dict__.get('discord_webhook') or 
            os.getenv('DISCORD_WEBHOOK') or 
            os.getenv('DISCORD_WEBHOOK_URL')
        )
        self.enabled = bool(self.webhook_url)
        
        # 判斷當前交易模式
        self.trading_mode = self._get_trading_mode()
        
        if self.enabled:
            logger.info(f"✅ Discord 通知已啟用 - 交易模式: {self.trading_mode}")
        else:
            logger.warning("⚠️  Discord webhook 未配置")
    
    def _get_trading_mode(self) -> str:
        """獲取當前交易模式"""
        if config.binance.demo_mode:
            return "🎮 Demo 模式"
        elif config.binance.paper_trading:
            return "📋 紙上交易"
        elif config.binance.testnet:
            return "🧪 Testnet"
        else:
            return "🔴 真實交易"
    
    def send_message(self, content: str, embed: Optional[Dict[str, Any]] = None) -> bool:
        """發送訊息到 Discord"""
        if not self.enabled:
            logger.debug("Discord webhook not configured, skipping notification")
            return False
            
        try:
            payload = {
                "content": content,
                "username": f"Binance Trading Bot ({self.trading_mode})",
                "avatar_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
            
            if embed:
                payload["embeds"] = [embed]
                
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:
                logger.success("Discord message sent successfully")
                return True
            else:
                logger.error(f"Discord webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False
    
    def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """發送交易通知"""
        if not self.enabled:
            return False
        
        # 根據交易模式設置不同的顏色和前綴
        mode_config = {
            "🎮 Demo 模式": {"color": 0x9932cc, "prefix": "🎮"},
            "📋 紙上交易": {"color": 0x1e90ff, "prefix": "📋"},
            "🧪 Testnet": {"color": 0xffa500, "prefix": "🧪"},
            "🔴 真實交易": {"color": 0xff0000, "prefix": "🔴"}
        }
        
        mode_info = mode_config.get(self.trading_mode, {"color": 0x808080, "prefix": "?"})
        
        side = trade_data.get('side', 'UNKNOWN')
        emoji = "🟢" if side == 'BUY' else "🔴" if side == 'SELL' else "⚪"
        
        embed = {
            "title": f"{mode_info['prefix']} 交易執行 - {emoji} {side}",
            "color": 0x00ff00 if side == 'BUY' else 0xff0000,
            "fields": [
                {
                    "name": "交易模式", 
                    "value": self.trading_mode, 
                    "inline": True
                },
                {
                    "name": "交易對", 
                    "value": trade_data.get('symbol', 'N/A'), 
                    "inline": True
                },
                {
                    "name": "數量", 
                    "value": f"{trade_data.get('quantity', 'N/A')}", 
                    "inline": True
                },
                {
                    "name": "價格", 
                    "value": f"${float(trade_data.get('price', 0)):,.2f}" if trade_data.get('price') else 'N/A', 
                    "inline": True
                },
                {
                    "name": "總金額", 
                    "value": f"${float(trade_data.get('quantity', 0)) * float(trade_data.get('price', 0)):,.2f}" if trade_data.get('quantity') and trade_data.get('price') else 'N/A', 
                    "inline": True
                },
                {
                    "name": "手續費", 
                    "value": f"${float(trade_data.get('commission', 0)):.4f}" if trade_data.get('commission') else 'N/A', 
                    "inline": True
                },
                {
                    "name": "策略", 
                    "value": trade_data.get('strategy', 'N/A'), 
                    "inline": True
                },
                {
                    "name": "訂單 ID", 
                    "value": str(trade_data.get('order_id', 'N/A')), 
                    "inline": True
                },
                {
                    "name": "時間", 
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "inline": False
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"Binance Trading Bot | {self.trading_mode}",
                "icon_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
        }
        
        # 添加交易模式說明
        if self.trading_mode in ["🎮 Demo 模式", "📋 紙上交易"]:
            embed["description"] = "⚠️ 此為模擬交易，不涉及真實資金"
        elif self.trading_mode == "🧪 Testnet":
            embed["description"] = "🧪 此為測試網交易"
        else:
            embed["description"] = "🔴 **真實交易警告** - 涉及真實資金"
        
        return self.send_message("", embed)
    
    def send_strategy_signal(self, signal_data: Dict[str, Any]) -> bool:
        """發送策略信號通知"""
        if not self.enabled:
            return False
        
        signal_type = signal_data.get('signal', 'UNKNOWN')
        symbol = signal_data.get('symbol', 'N/A')
        reason = signal_data.get('reason', 'N/A')
        confidence = signal_data.get('confidence', 0)
        
        emoji_map = {
            'BUY': '🟢',
            'SELL': '🔴',
            'HOLD': '🟡',
            'UNKNOWN': '⚪'
        }
        
        embed = {
            "title": f"📊 策略信號 - {emoji_map.get(signal_type, '⚪')} {signal_type}",
            "color": 0x00ff00 if signal_type == 'BUY' else 0xff0000 if signal_type == 'SELL' else 0xffff00,
            "fields": [
                {"name": "交易模式", "value": self.trading_mode, "inline": True},
                {"name": "交易對", "value": symbol, "inline": True},
                {"name": "信號強度", "value": f"{confidence:.2%}", "inline": True},
                {"name": "信號原因", "value": reason, "inline": False},
                {"name": "時間", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"Strategy Signal | {self.trading_mode}",
                "icon_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
        }
        
        return self.send_message("", embed)
    
    def send_portfolio_update(self, portfolio_data: Dict[str, Any]) -> bool:
        """發送投資組合更新"""
        if not self.enabled:
            return False
        
        embed = {
            "title": f"💼 投資組合更新 ({self.trading_mode})",
            "color": 0x1e90ff,
            "fields": [
                {
                    "name": "總資產價值", 
                    "value": f"${float(portfolio_data.get('total_value', 0)):,.2f}", 
                    "inline": True
                },
                {
                    "name": "可用餘額", 
                    "value": f"${float(portfolio_data.get('available_balance', 0)):,.2f}", 
                    "inline": True
                },
                {
                    "name": "未實現盈虧", 
                    "value": f"${float(portfolio_data.get('unrealized_pnl', 0)):+,.4f}", 
                    "inline": True
                },
                {
                    "name": "今日盈虧", 
                    "value": f"${float(portfolio_data.get('daily_pnl', 0)):+,.4f}", 
                    "inline": True
                },
                {
                    "name": "總盈虧百分比", 
                    "value": f"{float(portfolio_data.get('pnl_percentage', 0)):+.2f}%", 
                    "inline": True
                },
                {
                    "name": "活躍持倉", 
                    "value": str(portfolio_data.get('active_positions', 0)), 
                    "inline": True
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"Portfolio Update | {self.trading_mode}",
                "icon_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
        }
        
        return self.send_message("", embed)
    
    def send_system_alert(self, message: str, level: str = "info") -> bool:
        """發送系統警告通知"""
        if not self.enabled:
            return False
        
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌",
            "critical": "🚨"
        }
        
        color_map = {
            "info": 0x3498db,
            "success": 0x2ecc71,
            "warning": 0xf39c12,
            "error": 0xe74c3c,
            "critical": 0x8b0000
        }
        
        embed = {
            "title": f"{emoji_map.get(level, 'ℹ️')} 系統通知",
            "description": message,
            "color": color_map.get(level, 0x3498db),
            "fields": [
                {"name": "交易模式", "value": self.trading_mode, "inline": True},
                {"name": "警告等級", "value": level.upper(), "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"System Alert | {self.trading_mode}",
                "icon_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
        }
        
        return self.send_message("", embed)
    
    def send_startup_notification(self) -> bool:
        """發送系統啟動通知"""
        if not self.enabled:
            return False
        
        embed = {
            "title": "🚀 Binance Trading Bot 已啟動",
            "color": 0x00ff00,
            "fields": [
                {"name": "交易模式", "value": self.trading_mode, "inline": True},
                {"name": "時間", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"Bot Startup | {self.trading_mode}",
                "icon_url": "https://cryptologos.cc/logos/binance-coin-bnb-logo.png"
            }
        }
        
        if self.trading_mode in ["🎮 Demo 模式", "📋 紙上交易"]:
            embed["description"] = "✅ 安全模式啟動 - 無真實資金風險"
        elif self.trading_mode == "🧪 Testnet":
            embed["description"] = "🧪 測試網模式啟動"
        else:
            embed["description"] = "🔴 **真實交易模式** - 請謹慎操作"
        
        return self.send_message("", embed)
    
    def test_webhook(self) -> bool:
        """測試 webhook 連接"""
        return self.send_system_alert(
            f"Discord webhook 測試成功！當前交易模式: {self.trading_mode}", 
            "success"
        )


# 全域通知器實例
import os
discord_notifier = DiscordNotifier()
