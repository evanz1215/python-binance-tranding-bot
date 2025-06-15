"""
Database models for the trading bot
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, JSON, ForeignKey, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class Symbol(Base):
    """Symbol information table"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    min_qty = Column(Float)
    max_qty = Column(Float)
    step_size = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    tick_size = Column(Float)
    min_notional = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="symbol_info")
    positions = relationship("Position", back_populates="symbol_info")
    market_data = relationship("MarketData", back_populates="symbol_info")


class Strategy(Base):
    """Trading strategies table"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    parameters = Column(JSON)  # Strategy-specific parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="strategy")
    positions = relationship("Position", back_populates="strategy")
    backtests = relationship("Backtest", back_populates="strategy")


class Position(Base):
    """Open positions table"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey("symbols.symbol"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, PARTIAL
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Relationships
    symbol_info = relationship("Symbol", back_populates="positions")
    strategy = relationship("Strategy", back_populates="positions")
    trades = relationship("Trade", back_populates="position")


class Trade(Base):
    """Executed trades table"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey("symbols.symbol"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"))
    order_id = Column(String(50), unique=True)
    side = Column(String(10), nullable=False)  # BUY or SELL
    type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS, etc.
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    realized_pnl = Column(Float)
    status = Column(String(20), nullable=False)  # FILLED, CANCELLED, REJECTED
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    symbol_info = relationship("Symbol", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    position = relationship("Position", back_populates="trades")


class MarketData(Base):
    """Market data (OHLCV) table"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), ForeignKey("symbols.symbol"), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades_count = Column(Integer)
    
    # Relationships
    symbol_info = relationship("Symbol", back_populates="market_data")
    
    __table_args__ = (
        Index('idx_symbol_timeframe_time', 'symbol', 'timeframe', 'open_time'),
    )


class Backtest(Base):
    """Backtest results table"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_balance = Column(Float, nullable=False)
    final_balance = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    parameters = Column(JSON)  # Backtest parameters
    results = Column(JSON)  # Detailed results
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")


class TradingSession(Base):
    """Trading session tracking"""
    __tablename__ = "trading_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    initial_balance = Column(Float)
    current_balance = Column(Float)
    total_pnl = Column(Float, default=0.0)
    trades_count = Column(Integer, default=0)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, PAUSED, STOPPED
    notes = Column(Text)


def create_database(database_url: str):
    """Create database and tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(database_url: str):
    """Get database session factory"""
    engine = create_database(database_url)
    return sessionmaker(bind=engine)
