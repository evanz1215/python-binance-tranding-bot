"""
Risk management system for the trading bot
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .config import config
from .binance_client import binance_client
from .database.models import Position, Trade, TradingSession


@dataclass
class RiskMetrics:
    """Risk metrics for portfolio"""
    total_balance: float
    available_balance: float
    total_positions_value: float
    daily_pnl: float
    total_pnl: float
    max_drawdown: float
    position_count: int
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class RiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self):
        self.daily_start_balance = None
        self.session_start_balance = None
        self.max_balance_today = None
        self.positions = {}  # symbol -> position info
        self.daily_trades = []
        
    def initialize_session(self) -> None:
        """Initialize risk management for new trading session"""
        try:
            # Get current balance
            balance = binance_client.get_balance(config.trading.base_currency)
            current_balance = balance.get('total', 0.0)
            
            # Set session start balance
            self.session_start_balance = current_balance
            
            # Set daily start balance if not set today
            today = datetime.utcnow().date()
            if (self.daily_start_balance is None or 
                not hasattr(self, 'daily_start_date') or 
                self.daily_start_date != today):
                self.daily_start_balance = current_balance
                self.max_balance_today = current_balance
                self.daily_start_date = today
                self.daily_trades = []
            
            # Update max balance
            if current_balance > self.max_balance_today:
                self.max_balance_today = current_balance
                
            logger.info(f"Risk management initialized - Balance: {current_balance:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to initialize risk management: {e}")
            raise
    
    def get_current_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        try:
            # Get current balance
            balance = binance_client.get_balance(config.trading.base_currency)
            total_balance = balance.get('total', 0.0)
            available_balance = balance.get('free', 0.0)
            
            # Calculate position values
            total_positions_value = self._calculate_positions_value()
            
            # Calculate PnL
            daily_pnl = total_balance - self.daily_start_balance if self.daily_start_balance else 0.0
            total_pnl = total_balance - self.session_start_balance if self.session_start_balance else 0.0
            
            # Calculate max drawdown
            max_drawdown = 0.0
            if self.max_balance_today:
                drawdown = (self.max_balance_today - total_balance) / self.max_balance_today
                max_drawdown = max(drawdown, 0.0)
            
            # Determine risk level
            risk_level = self._assess_risk_level(daily_pnl, total_balance, max_drawdown)
            
            return RiskMetrics(
                total_balance=total_balance,
                available_balance=available_balance,
                total_positions_value=total_positions_value,
                daily_pnl=daily_pnl,
                total_pnl=total_pnl,
                max_drawdown=max_drawdown,
                position_count=len(self.positions),
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            raise
    
    def can_open_position(self, symbol: str, side: str, amount: float) -> Tuple[bool, str]:
        """Check if we can open a new position"""
        try:
            metrics = self.get_current_metrics()
            
            # Check if trading is halted due to risk
            if metrics.risk_level == "CRITICAL":
                return False, "Trading halted due to critical risk level"
            
            # Check daily loss limit
            daily_loss_pct = abs(metrics.daily_pnl) / self.daily_start_balance if self.daily_start_balance else 0
            if metrics.daily_pnl < 0 and daily_loss_pct > config.trading.max_daily_loss_pct:
                return False, f"Daily loss limit exceeded: {daily_loss_pct:.2%}"
            
            # Check max drawdown
            if metrics.max_drawdown > config.trading.max_drawdown_pct:
                return False, f"Max drawdown exceeded: {metrics.max_drawdown:.2%}"
            
            # Check maximum positions
            if metrics.position_count >= config.trading.max_positions:
                return False, f"Maximum positions reached: {metrics.position_count}"
            
            # Check if we already have a position in this symbol
            if symbol in self.positions:
                return False, f"Already have position in {symbol}"
            
            # Check available balance
            if amount > metrics.available_balance:
                return False, f"Insufficient balance: {amount:.2f} > {metrics.available_balance:.2f}"
            
            # Check position size limits
            position_pct = amount / metrics.total_balance
            max_position_pct = config.trading.position_size_pct * 2  # Allow up to 2x normal size
            if position_pct > max_position_pct:
                return False, f"Position size too large: {position_pct:.2%} > {max_position_pct:.2%}"
            
            return True, "Position approved"
            
        except Exception as e:
            logger.error(f"Error checking position approval: {e}")
            return False, f"Risk check failed: {e}"
    
    def can_close_position(self, symbol: str) -> Tuple[bool, str]:
        """Check if we can close a position"""
        try:
            if symbol not in self.positions:
                return False, f"No position found for {symbol}"
            
            # Generally, we should always be able to close positions
            # unless there are severe technical issues
            return True, "Position closure approved"
            
        except Exception as e:
            logger.error(f"Error checking position closure: {e}")
            return False, f"Risk check failed: {e}"
    
    def calculate_stop_loss(self, symbol: str, side: str, entry_price: float) -> float:
        """Calculate stop loss price"""
        try:
            stop_loss_pct = config.trading.stop_loss_pct
            
            if side.upper() == "BUY":
                # For long positions, stop loss is below entry price
                stop_loss = entry_price * (1 - stop_loss_pct)
            else:
                # For short positions, stop loss is above entry price
                stop_loss = entry_price * (1 + stop_loss_pct)
            
            return stop_loss
            
        except Exception as e:
            logger.error(f"Error calculating stop loss for {symbol}: {e}")
            return entry_price  # Fallback to entry price
    
    def calculate_take_profit(self, symbol: str, side: str, entry_price: float) -> float:
        """Calculate take profit price"""
        try:
            take_profit_pct = config.trading.take_profit_pct
            
            if side.upper() == "BUY":
                # For long positions, take profit is above entry price
                take_profit = entry_price * (1 + take_profit_pct)
            else:
                # For short positions, take profit is below entry price
                take_profit = entry_price * (1 - take_profit_pct)
            
            return take_profit
            
        except Exception as e:
            logger.error(f"Error calculating take profit for {symbol}: {e}")
            return entry_price  # Fallback to entry price
    
    def add_position(self, symbol: str, side: str, quantity: float, 
                    entry_price: float, stop_loss: float = None, 
                    take_profit: float = None) -> None:
        """Add a new position to tracking"""
        try:
            if stop_loss is None:
                stop_loss = self.calculate_stop_loss(symbol, side, entry_price)
            
            if take_profit is None:
                take_profit = self.calculate_take_profit(symbol, side, entry_price)
            
            self.positions[symbol] = {
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'opened_at': datetime.utcnow()
            }
            
            logger.info(f"Added position: {symbol} {side} {quantity} @ {entry_price}")
            
        except Exception as e:
            logger.error(f"Error adding position {symbol}: {e}")
    
    def remove_position(self, symbol: str) -> None:
        """Remove position from tracking"""
        try:
            if symbol in self.positions:
                del self.positions[symbol]
                logger.info(f"Removed position: {symbol}")
            
        except Exception as e:
            logger.error(f"Error removing position {symbol}: {e}")
    
    def update_position_prices(self, symbol: str, current_price: float) -> Dict[str, bool]:
        """Update position with current price and check stop/take profit triggers"""
        try:
            if symbol not in self.positions:
                return {'stop_loss_triggered': False, 'take_profit_triggered': False}
            
            position = self.positions[symbol]
            side = position['side']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            
            stop_loss_triggered = False
            take_profit_triggered = False
            
            if side.upper() == "BUY":
                # Long position
                if current_price <= stop_loss:
                    stop_loss_triggered = True
                elif current_price >= take_profit:
                    take_profit_triggered = True
            else:
                # Short position
                if current_price >= stop_loss:
                    stop_loss_triggered = True
                elif current_price <= take_profit:
                    take_profit_triggered = True
            
            # Update position with current price
            position['current_price'] = current_price
            position['unrealized_pnl'] = self._calculate_unrealized_pnl(position, current_price)
            
            return {
                'stop_loss_triggered': stop_loss_triggered,
                'take_profit_triggered': take_profit_triggered
            }
            
        except Exception as e:
            logger.error(f"Error updating position prices for {symbol}: {e}")
            return {'stop_loss_triggered': False, 'take_profit_triggered': False}
    
    def _calculate_positions_value(self) -> float:
        """Calculate total value of all positions"""
        try:
            total_value = 0.0
            
            for symbol, position in self.positions.items():
                try:
                    # Get current price
                    ticker = binance_client.get_24hr_ticker(symbol)
                    current_price = float(ticker['lastPrice'])
                    
                    # Calculate position value
                    position_value = position['quantity'] * current_price
                    total_value += position_value
                    
                except Exception as e:
                    logger.warning(f"Could not get price for {symbol}: {e}")
                    # Use entry price as fallback
                    position_value = position['quantity'] * position['entry_price']
                    total_value += position_value
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating positions value: {e}")
            return 0.0
    
    def _calculate_unrealized_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate unrealized PnL for a position"""
        try:
            entry_price = position['entry_price']
            quantity = position['quantity']
            side = position['side']
            
            if side.upper() == "BUY":
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity
            
            return pnl
            
        except Exception as e:
            logger.error(f"Error calculating unrealized PnL: {e}")
            return 0.0
    
    def _assess_risk_level(self, daily_pnl: float, total_balance: float, 
                          max_drawdown: float) -> str:
        """Assess current risk level"""
        try:
            # Check daily loss
            daily_loss_pct = abs(daily_pnl) / self.daily_start_balance if self.daily_start_balance and daily_pnl < 0 else 0
            
            # Critical level
            if (daily_loss_pct > config.trading.max_daily_loss_pct * 0.9 or 
                max_drawdown > config.trading.max_drawdown_pct * 0.9):
                return "CRITICAL"
            
            # High level
            if (daily_loss_pct > config.trading.max_daily_loss_pct * 0.7 or 
                max_drawdown > config.trading.max_drawdown_pct * 0.7):
                return "HIGH"
            
            # Medium level
            if (daily_loss_pct > config.trading.max_daily_loss_pct * 0.5 or 
                max_drawdown > config.trading.max_drawdown_pct * 0.5):
                return "MEDIUM"
            
            return "LOW"
            
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "HIGH"  # Default to high risk if we can't assess
    
    def get_risk_report(self) -> Dict:
        """Get comprehensive risk report"""
        try:
            metrics = self.get_current_metrics()
            
            return {
                'timestamp': datetime.utcnow(),
                'metrics': metrics,
                'positions': self.positions,
                'limits': {
                    'max_daily_loss_pct': config.trading.max_daily_loss_pct,
                    'max_drawdown_pct': config.trading.max_drawdown_pct,
                    'max_positions': config.trading.max_positions,
                    'position_size_pct': config.trading.position_size_pct
                },
                'recommendations': self._get_recommendations(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {}
    
    def _get_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Get risk management recommendations"""
        recommendations = []
        
        try:
            if metrics.risk_level == "CRITICAL":
                recommendations.append("CRITICAL: Consider halting all trading immediately")
                recommendations.append("Review and reduce position sizes")
                recommendations.append("Check for system errors or unusual market conditions")
            
            elif metrics.risk_level == "HIGH":
                recommendations.append("HIGH RISK: Reduce position sizes")
                recommendations.append("Consider closing losing positions")
                recommendations.append("Avoid opening new positions until risk decreases")
            
            elif metrics.risk_level == "MEDIUM":
                recommendations.append("MEDIUM RISK: Monitor positions closely")
                recommendations.append("Consider tighter stop losses")
                recommendations.append("Be selective with new positions")
            
            if metrics.position_count >= config.trading.max_positions * 0.8:
                recommendations.append("Approaching maximum position limit")
            
            if metrics.daily_pnl < 0:
                daily_loss_pct = abs(metrics.daily_pnl) / self.daily_start_balance if self.daily_start_balance else 0
                recommendations.append(f"Daily loss: {daily_loss_pct:.2%}")
            
            if not recommendations:
                recommendations.append("Risk levels are within acceptable limits")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations")
        
        return recommendations


# Global risk manager instance
risk_manager = RiskManager()
