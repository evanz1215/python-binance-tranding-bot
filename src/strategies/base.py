"""
Base strategy class and common strategy implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..database.models import Position


class Signal:
    """Trading signal class"""
    def __init__(self, symbol: str, action: str, strength: float, 
                 reason: str, timestamp: datetime | None = None):
        self.symbol = symbol
        self.action = action  # BUY, SELL, HOLD
        self.strength = strength  # 0.0 to 1.0
        self.reason = reason
        self.timestamp = timestamp or datetime.utcnow()
    
    def __repr__(self):
        return f"Signal({self.symbol}, {self.action}, {self.strength:.2f}, {self.reason})"


class BaseStrategy(ABC):
    """Base strategy class that all strategies must inherit from"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] | None = None):
        self.name = name
        self.parameters = parameters or {}
        self.positions = {}  # symbol -> position info
        self.last_signals = {}  # symbol -> last signal
        
    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """
        Analyze market data and return trading signal
        
        Args:
            symbol: Trading symbol
            data: OHLCV data as pandas DataFrame
            
        Returns:
            Signal object with trading decision
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_required_timeframes(self) -> List[str]:
        """Return list of required timeframes for this strategy"""
        raise NotImplementedError
    
    @abstractmethod
    def get_required_periods(self) -> int:
        """Return minimum number of periods required for analysis"""
        raise NotImplementedError
    
    def should_enter_position(self, symbol: str, signal: Signal, 
                            current_balance: float) -> bool:
        """
        Determine if we should enter a new position
        
        Args:
            symbol: Trading symbol
            signal: Current trading signal
            current_balance: Available balance
            
        Returns:
            True if should enter position
        """
        if signal.action == "HOLD":
            return False
            
        if symbol in self.positions:
            return False  # Already have position
            
        if signal.strength < 0.6:  # Minimum signal strength
            return False
            
        return True
    
    def should_exit_position(self, symbol: str, signal: Signal, 
                           position: Position) -> bool:
        """
        Determine if we should exit existing position
        
        Args:
            symbol: Trading symbol
            signal: Current trading signal
            position: Current position
            
        Returns:
            True if should exit position
        """
        if signal.action == "HOLD":
            return False
              # Exit if signal is opposite to position
        position_side = str(position.side) if hasattr(position, 'side') else position.get('side', '')
        if (position_side == "BUY" and signal.action == "SELL") or \
           (position_side == "SELL" and signal.action == "BUY"):
            return True
            
        return False
    
    def calculate_position_size(self, symbol: str, signal: Signal, 
                              available_balance: float, price: float) -> float:
        """
        Calculate position size based on signal strength and risk management
        
        Args:
            symbol: Trading symbol
            signal: Trading signal
            available_balance: Available balance
            price: Current price
            
        Returns:
            Position size in USDT
        """
        from ..config import config
        
        # Base position size
        base_size = available_balance * config.trading.position_size_pct
        
        # Adjust based on signal strength
        adjusted_size = base_size * signal.strength
        
        # Maximum position size
        max_size = available_balance * 0.2  # Never more than 20% per position
        
        return min(adjusted_size, max_size)


class MovingAverageCrossStrategy(BaseStrategy):
    """Simple moving average crossover strategy"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26):
        super().__init__("MA_Cross", {
            "fast_period": fast_period,
            "slow_period": slow_period
        })
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def get_required_timeframes(self) -> List[str]:
        return ["15m"]
    
    def get_required_periods(self) -> int:
        return max(self.fast_period, self.slow_period) + 10
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Analyze using moving average crossover"""
        try:
            if len(data) < self.get_required_periods():
                return Signal(symbol, "HOLD", 0.0, "Insufficient data")
            
            # Calculate moving averages
            data['ma_fast'] = data['close'].rolling(window=self.fast_period).mean()
            data['ma_slow'] = data['close'].rolling(window=self.slow_period).mean()
            
            # Get latest values
            current_fast = data['ma_fast'].iloc[-1]
            current_slow = data['ma_slow'].iloc[-1]
            prev_fast = data['ma_fast'].iloc[-2]
            prev_slow = data['ma_slow'].iloc[-2]
            
            # Check for crossover
            if prev_fast <= prev_slow and current_fast > current_slow:
                # Bullish crossover
                strength = min(0.8, (current_fast - current_slow) / current_slow * 10)
                return Signal(symbol, "BUY", strength, "MA bullish crossover")
            elif prev_fast >= prev_slow and current_fast < current_slow:
                # Bearish crossover
                strength = min(0.8, (current_slow - current_fast) / current_fast * 10)
                return Signal(symbol, "SELL", strength, "MA bearish crossover")
            else:
                return Signal(symbol, "HOLD", 0.0, "No crossover signal")
                
        except Exception as e:
            logger.error("Error in MA Cross analysis for %s: %s", symbol, e)
            return Signal(symbol, "HOLD", 0.0, f"Analysis error: {e}")


class RSIStrategy(BaseStrategy):
    """RSI-based trading strategy"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI", {
            "period": period,
            "oversold": oversold,
            "overbought": overbought
        })
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def get_required_timeframes(self) -> List[str]:
        return ["1h"]
    
    def get_required_periods(self) -> int:
        return self.period + 20
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Analyze using RSI"""
        try:
            if len(data) < self.get_required_periods():
                return Signal(symbol, "HOLD", 0.0, "Insufficient data")
            
            # Simple RSI calculation fallback
            data['rsi'] = self._calculate_rsi(data['close'], self.period)
            
            current_rsi = data['rsi'].iloc[-1]
            prev_rsi = data['rsi'].iloc[-2]
            
            if current_rsi < self.oversold and prev_rsi >= self.oversold:
                strength = min(0.9, (self.oversold - current_rsi) / self.oversold)
                return Signal(symbol, "BUY", strength, f"RSI oversold: {current_rsi:.1f}")
            elif current_rsi > self.overbought and prev_rsi <= self.overbought:
                strength = min(0.9, (current_rsi - self.overbought) / (100 - self.overbought))
                return Signal(symbol, "SELL", strength, f"RSI overbought: {current_rsi:.1f}")
            else:
                return Signal(symbol, "HOLD", 0.0, f"RSI neutral: {current_rsi:.1f}")
                
        except Exception as e:
            logger.error("Error in RSI analysis for %s: %s", symbol, e)
            return Signal(symbol, "HOLD", 0.0, f"Analysis error: {e}")
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI manually"""
        delta = prices.diff()
        # Use explicit numeric comparison to avoid type issues
        gain = delta.where(delta > 0, 0.0).ewm(span=period).mean()  # type: ignore
        loss = (-delta.where(delta < 0, 0.0)).ewm(span=period).mean()  # type: ignore
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi


class MACDStrategy(BaseStrategy):
    """MACD-based trading strategy"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD", {
            "fast": fast,
            "slow": slow,
            "signal": signal
        })
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
    
    def get_required_timeframes(self) -> List[str]:
        return ["4h"]
    
    def get_required_periods(self) -> int:
        return self.slow + self.signal_period + 10
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Analyze using MACD"""
        try:
            if len(data) < self.get_required_periods():
                return Signal(symbol, "HOLD", 0.0, "Insufficient data")
              # Calculate MACD manually
            ema_fast = data['close'].ewm(span=self.fast).mean()
            ema_slow = data['close'].ewm(span=self.slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            histogram = macd_line - signal_line
            
            data['macd'] = macd_line
            data['macd_signal'] = signal_line
            data['macd_histogram'] = histogram
            
            current_macd = data['macd'].iloc[-1]
            current_signal = data['macd_signal'].iloc[-1]
            prev_macd = data['macd'].iloc[-2]
            prev_signal = data['macd_signal'].iloc[-2]
            
            # Check for signal line crossover
            if prev_macd <= prev_signal and current_macd > current_signal:
                # Bullish crossover
                strength = min(0.8, abs(current_macd - current_signal) / abs(current_signal) * 5)
                return Signal(symbol, "BUY", strength, "MACD bullish crossover")
            elif prev_macd >= prev_signal and current_macd < current_signal:
                # Bearish crossover
                strength = min(0.8, abs(current_signal - current_macd) / abs(current_macd) * 5)
                return Signal(symbol, "SELL", strength, "MACD bearish crossover")
            else:
                return Signal(symbol, "HOLD", 0.0, "No MACD signal")
                
        except Exception as e:
            logger.error("Error in MACD analysis for %s: %s", symbol, e)
            return Signal(symbol, "HOLD", 0.0, f"Analysis error: {e}")


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("BollingerBands", {
            "period": period,
            "std_dev": std_dev
        })
        self.period = period
        self.std_dev = std_dev
    
    def get_required_timeframes(self) -> List[str]:
        return ["1h"]
    
    def get_required_periods(self) -> int:
        return self.period + 10
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Analyze using Bollinger Bands"""
        try:
            if len(data) < self.get_required_periods():
                return Signal(symbol, "HOLD", 0.0, "Insufficient data")
            
            # Calculate Bollinger Bands manually
            sma = data['close'].rolling(window=self.period).mean()
            std = data['close'].rolling(window=self.period).std()
            
            data['bb_upper'] = sma + (std * self.std_dev)
            data['bb_lower'] = sma - (std * self.std_dev)
            data['bb_middle'] = sma
            
            current_price = data['close'].iloc[-1]
            bb_upper = data['bb_upper'].iloc[-1]
            bb_lower = data['bb_lower'].iloc[-1]
            
            # Calculate position relative to bands
            if current_price <= bb_lower:
                # Price at or below lower band - potential buy
                strength = min(0.8, (bb_lower - current_price) / bb_lower * 20)
                return Signal(symbol, "BUY", strength, "Price at lower Bollinger Band")
            elif current_price >= bb_upper:
                # Price at or above upper band - potential sell
                strength = min(0.8, (current_price - bb_upper) / bb_upper * 20)
                return Signal(symbol, "SELL", strength, "Price at upper Bollinger Band")
            else:
                return Signal(symbol, "HOLD", 0.0, "Price within Bollinger Bands")
                
        except Exception as e:
            logger.error("Error in Bollinger Bands analysis for %s: %s", symbol, e)
            return Signal(symbol, "HOLD", 0.0, f"Analysis error: {e}")


class CombinedStrategy(BaseStrategy):
    """Combined strategy using multiple indicators"""
    
    def __init__(self):
        super().__init__("Combined", {})
        self.ma_strategy = MovingAverageCrossStrategy()
        self.rsi_strategy = RSIStrategy()
        self.macd_strategy = MACDStrategy()
        self.bb_strategy = BollingerBandsStrategy()
    
    def get_required_timeframes(self) -> List[str]:
        return ["15m", "1h", "4h"]
    
    def get_required_periods(self) -> int:
        return 100  # Enough for all sub-strategies
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> Signal:
        """Analyze using combined signals"""
        try:
            # Get signals from all strategies
            ma_signal = self.ma_strategy.analyze(symbol, data)
            rsi_signal = self.rsi_strategy.analyze(symbol, data)
            macd_signal = self.macd_strategy.analyze(symbol, data)
            bb_signal = self.bb_strategy.analyze(symbol, data)
            
            signals = [ma_signal, rsi_signal, macd_signal, bb_signal]
            
            # Count signals
            buy_signals = [s for s in signals if s.action == "BUY"]
            sell_signals = [s for s in signals if s.action == "SELL"]
            
            # Combine signals
            if len(buy_signals) >= 2:
                avg_strength = sum(s.strength for s in buy_signals) / len(buy_signals)
                reasons = [s.reason for s in buy_signals]
                return Signal(symbol, "BUY", avg_strength, f"Combined: {', '.join(reasons)}")
            elif len(sell_signals) >= 2:
                avg_strength = sum(s.strength for s in sell_signals) / len(sell_signals)
                reasons = [s.reason for s in sell_signals]
                return Signal(symbol, "SELL", avg_strength, f"Combined: {', '.join(reasons)}")
            else:
                return Signal(symbol, "HOLD", 0.0, "Conflicting or weak signals")
                
        except Exception as e:
            logger.error("Error in Combined strategy analysis for %s: %s", symbol, e)
            return Signal(symbol, "HOLD", 0.0, f"Analysis error: {e}")


# Strategy registry
STRATEGIES = {
    "ma_cross": MovingAverageCrossStrategy,
    "rsi": RSIStrategy,
    "macd": MACDStrategy,
    "bollinger_bands": BollingerBandsStrategy,
    "combined": CombinedStrategy
}


def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """Get strategy instance by name"""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    return STRATEGIES[strategy_name](**kwargs)
