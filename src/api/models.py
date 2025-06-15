"""
Pydantic models for API request/response
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class StrategyConfig(BaseModel):
    name: str
    parameters: Dict[str, Any] = {}


class BacktestRequest(BaseModel):
    strategy: StrategyConfig
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"
    initial_balance: float = 10000.0


class TradingStatus(BaseModel):
    is_running: bool
    session_id: Optional[str]
    strategy: str
    monitored_symbols: int
    active_positions: int
    risk_level: str
    total_balance: float
    daily_pnl: float
    last_update: datetime
