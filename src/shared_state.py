"""
Shared state management for the trading bot
"""

# Global trading engine instance
trading_engine = None

# Global paper trading client instance
paper_trading_client = None

def get_trading_engine():
    """Get the current trading engine instance"""
    return trading_engine

def set_trading_engine(engine):
    """Set the trading engine instance"""
    global trading_engine
    trading_engine = engine

def get_paper_trading_client():
    """Get the current paper trading client instance"""
    return paper_trading_client

def set_paper_trading_client(client):
    """Set the paper trading client instance"""
    global paper_trading_client
    paper_trading_client = client

def is_trading_active():
    """Check if trading is currently active"""
    return trading_engine is not None and hasattr(trading_engine, 'is_running') and trading_engine.is_running
