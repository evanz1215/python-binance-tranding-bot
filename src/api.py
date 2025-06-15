"""
Web API for the trading bot using FastAPI
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

try:
    import uvicorn
except ImportError:
    uvicorn = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .config import config
from .trading_engine import TradingEngine
from .backtest_engine import backtest_engine
from .risk_manager import risk_manager
from .data_manager import data_manager
from .binance_client import binance_client


# Pydantic models for API
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


# Global trading engine instance
trading_engine = None

# FastAPI app
app = FastAPI(
    title="Binance Trading Bot API",
    description="Automated trading bot with multiple strategies and backtesting",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Simple dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Binance Trading Bot</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
            .metric { text-align: center; }
            .metric h3 { margin: 0; color: #333; }
            .metric p { margin: 5px 0; font-size: 24px; font-weight: bold; }
            .running { color: #28a745; }
            .stopped { color: #dc3545; }
            .risk-low { color: #28a745; }
            .risk-medium { color: #ffc107; }
            .risk-high { color: #fd7e14; }
            .risk-critical { color: #dc3545; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-primary { background-color: #007bff; color: white; }
            .btn-danger { background-color: #dc3545; color: white; }
            .btn-success { background-color: #28a745; color: white; }
            .positions-table { width: 100%; border-collapse: collapse; }
            .positions-table th, .positions-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            .positions-table th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Binance Trading Bot Dashboard</h1>
            
            <div class="card">
                <h2>Bot Status</h2>
                <div class="status" id="status">
                    <!-- Status will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Controls</h2>
                <button class="btn-success" onclick="startBot()">Start Bot</button>
                <button class="btn-danger" onclick="stopBot()">Stop Bot</button>
                <button class="btn-primary" onclick="refreshData()">Refresh</button>
            </div>
            
            <div class="card">
                <h2>Risk Management</h2>
                <div id="risk-info">
                    <!-- Risk info will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Active Positions</h2>
                <div id="positions">
                    <!-- Positions will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Performance Chart</h2>
                <canvas id="performanceChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <script>
            let chart = null;
            
            async function fetchStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    updateStatus(data);
                } catch (error) {
                    console.error('Error fetching status:', error);
                }
            }
            
            async function fetchRiskInfo() {
                try {
                    const response = await fetch('/api/risk/report');
                    const data = await response.json();
                    updateRiskInfo(data);
                } catch (error) {
                    console.error('Error fetching risk info:', error);
                }
            }
            
            function updateStatus(data) {
                const statusDiv = document.getElementById('status');
                const statusClass = data.is_running ? 'running' : 'stopped';
                const riskClass = `risk-${data.risk_level.toLowerCase()}`;
                
                statusDiv.innerHTML = `
                    <div class="metric">
                        <h3>Status</h3>
                        <p class="${statusClass}">${data.is_running ? 'RUNNING' : 'STOPPED'}</p>
                    </div>
                    <div class="metric">
                        <h3>Strategy</h3>
                        <p>${data.strategy || 'N/A'}</p>
                    </div>
                    <div class="metric">
                        <h3>Symbols</h3>
                        <p>${data.monitored_symbols || 0}</p>
                    </div>
                    <div class="metric">
                        <h3>Positions</h3>
                        <p>${data.active_positions || 0}</p>
                    </div>
                    <div class="metric">
                        <h3>Balance</h3>
                        <p>$${(data.total_balance || 0).toFixed(2)}</p>
                    </div>
                    <div class="metric">
                        <h3>Daily P&L</h3>
                        <p class="${data.daily_pnl >= 0 ? 'running' : 'stopped'}">$${(data.daily_pnl || 0).toFixed(2)}</p>
                    </div>
                    <div class="metric">
                        <h3>Risk Level</h3>
                        <p class="${riskClass}">${data.risk_level || 'UNKNOWN'}</p>
                    </div>
                `;
            }
            
            function updateRiskInfo(data) {
                const riskDiv = document.getElementById('risk-info');
                if (data.recommendations) {
                    const recommendations = data.recommendations.map(r => `<li>${r}</li>`).join('');
                    riskDiv.innerHTML = `
                        <h4>Risk Recommendations:</h4>
                        <ul>${recommendations}</ul>
                    `;
                }
            }
            
            async function startBot() {
                try {
                    const response = await fetch('/api/trading/start', { method: 'POST' });
                    const result = await response.json();
                    alert(result.message || 'Bot started');
                    refreshData();
                } catch (error) {
                    alert('Error starting bot: ' + error.message);
                }
            }
            
            async function stopBot() {
                try {
                    const response = await fetch('/api/trading/stop', { method: 'POST' });
                    const result = await response.json();
                    alert(result.message || 'Bot stopped');
                    refreshData();
                } catch (error) {
                    alert('Error stopping bot: ' + error.message);
                }
            }
            
            function refreshData() {
                fetchStatus();
                fetchRiskInfo();
            }
            
            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {
                refreshData();
                
                // Auto-refresh every 30 seconds
                setInterval(refreshData, 30000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/status", response_model=TradingStatus)
async def get_status():
    """Get current trading bot status"""
    try:
        if trading_engine:
            status = trading_engine.get_status()
            return TradingStatus(**status)
        else:
            return TradingStatus(
                is_running=False,
                session_id=None,
                strategy="none",
                monitored_symbols=0,                active_positions=0,
                risk_level="UNKNOWN",
                total_balance=0.0,
                daily_pnl=0.0,
                last_update=datetime.utcnow()
            )
    except Exception as e:
        logger.error("Error getting status: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/trading/start")
async def start_trading(background_tasks: BackgroundTasks, strategy: Optional[StrategyConfig] = None):
    """Start the trading bot"""
    try:
        global trading_engine
        
        if trading_engine and trading_engine.is_running:
            return {"message": "Trading bot is already running"}
        
        # Create new trading engine
        if strategy:
            trading_engine = TradingEngine(strategy.name, **strategy.parameters)
        else:
            trading_engine = TradingEngine("ma_cross")  # Default strategy
          # Start in background
        background_tasks.add_task(trading_engine.start)
        
        return {"message": "Trading bot started successfully"}
        
    except Exception as e:
        logger.error("Error starting trading: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/trading/stop")
async def stop_trading():
    """Stop the trading bot"""
    try:
        global trading_engine
        
        if not trading_engine or not trading_engine.is_running:
            return {"message": "Trading bot is not running"}
        
        await trading_engine.stop()
        return {"message": "Trading bot stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/balance")
async def get_balance():
    """Get account balance"""
    try:
        balance = binance_client.get_balance()
        return {"balance": balance}
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    try:
        return {"positions": risk_manager.positions}
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/report")
async def get_risk_report():
    """Get risk management report"""
    try:
        report = risk_manager.get_risk_report()
        return report
    except Exception as e:
        logger.error(f"Error getting risk report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a backtest"""
    try:
        logger.info(f"Starting backtest for {request.strategy.name}")
        
        result = await backtest_engine.run_backtest(
            strategy_name=request.strategy.name,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            **request.strategy.parameters
        )
        
        # Convert result to dict for JSON response
        return {
            "strategy_name": result.strategy_name,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_balance": result.initial_balance,
            "final_balance": result.final_balance,
            "total_return": result.total_return,
            "total_return_pct": result.total_return_pct,
            "max_drawdown": result.max_drawdown,
            "max_drawdown_pct": result.max_drawdown_pct,
            "sharpe_ratio": result.sharpe_ratio,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "win_rate": result.win_rate,
            "avg_win": result.avg_win,
            "avg_loss": result.avg_loss,
            "profit_factor": result.profit_factor
        }
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/symbols")
async def get_symbols():
    """Get list of available symbols"""
    try:
        symbols = binance_client.filter_symbols_by_criteria(
            min_volume_24h=config.trading.min_volume_24h
        )
        return {"symbols": symbols}
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies")
async def get_strategies():
    """Get list of available strategies"""
    try:
        from .strategies import STRATEGIES
        
        strategies = []
        for name, strategy_class in STRATEGIES.items():
            strategies.append({
                "name": name,
                "description": strategy_class.__doc__ or f"{name} strategy"
            })
        
        return {"strategies": strategies}
    except Exception as e:
        logger.error("Error getting strategies: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/market-data/{symbol}/{timeframe}")
async def get_market_data(symbol: str, timeframe: str, limit: int = 100):
    """Get market data for a symbol"""
    try:
        df = data_manager.get_market_data(symbol, timeframe, limit=limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Convert to list of dicts for JSON response
        data = []
        for timestamp, row in df.iterrows():
            data.append({
                "timestamp": str(timestamp),
                "open": row['open'],
                "high": row['high'],
                "low": row['low'],
                "close": row['close'],
                "volume": row['volume']
            })
        
        return {"data": data}
        
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    logger.info("Starting API server on %s:%s", host, port)
    if uvicorn:
        uvicorn.run(app, host=host, port=port)
    else:
        logger.error("uvicorn not available, cannot start server")


if __name__ == "__main__":
    run_api_server()
