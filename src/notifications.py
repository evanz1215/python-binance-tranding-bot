"""
Notification system for trading bot alerts
"""
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import requests
from loguru import logger

from .config import config


class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    TRADE = "trade"
    RISK = "risk"


class NotificationManager:
    """Manages various notification channels"""
    
    def __init__(self):
        self.telegram_enabled = bool(
            config.notifications.telegram_bot_token and 
            config.notifications.telegram_chat_id
        )
        self.discord_enabled = bool(config.notifications.discord_webhook)
        
    async def send_notification(self, message: str, 
                              notification_type: NotificationType = NotificationType.INFO,
                              data: Optional[Dict[str, Any]] = None) -> None:
        """Send notification through all configured channels"""
        try:
            # Format message with timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            formatted_message = f"[{timestamp}] {message}"
            
            # Send to all enabled channels
            tasks = []
            
            if self.telegram_enabled:
                tasks.append(self._send_telegram(formatted_message, notification_type, data))
            
            if self.discord_enabled:
                tasks.append(self._send_discord(formatted_message, notification_type, data))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                logger.info(f"Notification: {formatted_message}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _send_telegram(self, message: str, notification_type: NotificationType,
                           data: Optional[Dict[str, Any]] = None) -> None:
        """Send notification via Telegram"""
        try:
            # Add emoji based on notification type
            emoji_map = {
                NotificationType.INFO: "ℹ️",
                NotificationType.WARNING: "⚠️",
                NotificationType.ERROR: "❌",
                NotificationType.TRADE: "💰",
                NotificationType.RISK: "🚨"
            }
            
            emoji = emoji_map.get(notification_type, "📢")
            formatted_message = f"{emoji} {message}"
            
            # Add data if provided
            if data:
                formatted_message += f"\n\n```json\n{json.dumps(data, indent=2, default=str)}\n```"
            
            url = f"https://api.telegram.org/bot{config.notifications.telegram_bot_token}/sendMessage"
            
            payload = {
                "chat_id": config.notifications.telegram_chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.debug("Telegram notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    async def _send_discord(self, message: str, notification_type: NotificationType,
                          data: Optional[Dict[str, Any]] = None) -> None:
        """Send notification via Discord webhook"""
        try:
            # Color based on notification type
            color_map = {
                NotificationType.INFO: 0x3498db,      # Blue
                NotificationType.WARNING: 0xf39c12,   # Orange
                NotificationType.ERROR: 0xe74c3c,     # Red
                NotificationType.TRADE: 0x2ecc71,     # Green
                NotificationType.RISK: 0x9b59b6       # Purple
            }
            
            color = color_map.get(notification_type, 0x95a5a6)  # Gray default
            
            embed = {
                "title": f"Trading Bot {notification_type.value.title()}",
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Binance Trading Bot"
                }
            }
            
            # Add data as fields if provided
            if data:
                embed["fields"] = []
                for key, value in data.items():
                    embed["fields"].append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True
                    })
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                config.notifications.discord_webhook, 
                json=payload, 
                timeout=10
            )
            response.raise_for_status()
            
            logger.debug("Discord notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
    
    async def notify_trade_executed(self, symbol: str, side: str, quantity: float,
                                  price: float, pnl: Optional[float] = None) -> None:
        """Send trade execution notification"""
        try:
            message = f"Trade Executed: {side} {quantity:.6f} {symbol} @ ${price:.4f}"
            
            if pnl is not None:
                pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
                message += f" (P&L: {pnl_str})"
            
            data = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "value": quantity * price
            }
            
            if pnl is not None:
                data["pnl"] = pnl
            
            await self.send_notification(message, NotificationType.TRADE, data)
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
    
    async def notify_risk_alert(self, risk_level: str, message: str, 
                              metrics: Optional[Dict[str, Any]] = None) -> None:
        """Send risk management alert"""
        try:
            alert_message = f"Risk Alert ({risk_level}): {message}"
            
            await self.send_notification(
                alert_message, 
                NotificationType.RISK, 
                metrics
            )
            
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
    
    async def notify_bot_status(self, status: str, details: Optional[str] = None) -> None:
        """Send bot status notification"""
        try:
            message = f"Bot Status: {status}"
            if details:
                message += f" - {details}"
            
            notification_type = NotificationType.INFO
            if status.lower() in ["stopped", "error", "crashed"]:
                notification_type = NotificationType.ERROR
            elif status.lower() in ["warning", "paused"]:
                notification_type = NotificationType.WARNING
            
            await self.send_notification(message, notification_type)
            
        except Exception as e:
            logger.error(f"Error sending status notification: {e}")
    
    async def notify_error(self, error_message: str, 
                         details: Optional[Dict[str, Any]] = None) -> None:
        """Send error notification"""
        try:
            await self.send_notification(
                f"Error: {error_message}", 
                NotificationType.ERROR, 
                details
            )
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    async def notify_daily_summary(self, summary: Dict[str, Any]) -> None:
        """Send daily trading summary"""
        try:
            total_pnl = summary.get('total_pnl', 0)
            total_trades = summary.get('total_trades', 0)
            win_rate = summary.get('win_rate', 0)
            
            pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"
            
            message = (
                f"Daily Summary:\n"
                f"P&L: {pnl_str}\n"
                f"Trades: {total_trades}\n"
                f"Win Rate: {win_rate:.1%}"
            )
            
            notification_type = NotificationType.TRADE if total_pnl >= 0 else NotificationType.WARNING
            
            await self.send_notification(message, notification_type, summary)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    async def test_notifications(self) -> Dict[str, bool]:
        """Test all notification channels"""
        results = {}
        
        try:
            test_message = "Test notification from Binance Trading Bot"
            
            if self.telegram_enabled:
                try:
                    await self._send_telegram(test_message, NotificationType.INFO)
                    results["telegram"] = True
                except Exception as e:
                    logger.error(f"Telegram test failed: {e}")
                    results["telegram"] = False
            else:
                results["telegram"] = False
            
            if self.discord_enabled:
                try:
                    await self._send_discord(test_message, NotificationType.INFO)
                    results["discord"] = True
                except Exception as e:
                    logger.error(f"Discord test failed: {e}")
                    results["discord"] = False
            else:
                results["discord"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing notifications: {e}")
            return {"error": str(e)}


# Global notification manager instance
notification_manager = NotificationManager()
