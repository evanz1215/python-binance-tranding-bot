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
from .data_manager_fixed import data_manager
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
    </head>    <body>
        <div class="container">
            <div style="background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px;">                <a href="/" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; background: #007bff;">Dashboard</a>
                <a href="/orders" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Orders</a>
                <a href="/positions" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Spot Positions</a>
                <a href="/futures" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Futures</a>
                <a href="/history" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">History</a>
            </div>
            
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
        logger.error(f"Error getting status: {e}")
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


@app.get("/orders", response_class=HTMLResponse)
async def orders_page():
    """Orders monitoring page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Bot - Orders Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav { background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px; }
            .nav a { color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .nav a.active { background: #007bff; }
            .orders-table { width: 100%; border-collapse: collapse; font-size: 14px; }
            .orders-table th, .orders-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            .orders-table th { background-color: #f8f9fa; font-weight: bold; }
            .orders-table tr:hover { background-color: #f5f5f5; }
            .status-new { background-color: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 3px; }
            .status-filled { background-color: #e8f5e8; color: #2e7d32; padding: 2px 6px; border-radius: 3px; }
            .status-canceled { background-color: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 3px; }
            .status-partial { background-color: #fff3e0; color: #f57c00; padding: 2px 6px; border-radius: 3px; }
            .side-buy { color: #2e7d32; font-weight: bold; }
            .side-sell { color: #c62828; font-weight: bold; }
            .refresh-btn { background: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin: 10px 0; }
            .refresh-btn:hover { background: #0056b3; }
            .filter-section { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px; }
            .filter-section select, .filter-section input { margin: 5px; padding: 5px; border: 1px solid #ddd; border-radius: 3px; }
            .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .summary-item { text-align: center; padding: 15px; background: #e9ecef; border-radius: 6px; }
            .summary-item h4 { margin: 0 0 8px 0; color: #495057; }
            .summary-item p { margin: 0; font-size: 18px; font-weight: bold; color: #212529; }
        </style>
    </head>
    <body>
        <div class="container">            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/orders">Orders</a>
                <a href="/positions">Positions</a>
                <a href="/history">History</a>
            </div>
            
            <h1>📋 Orders Monitor</h1>
            
            <div class="card">
                <h2>Order Summary</h2>
                <div class="summary" id="summary">
                    <!-- Summary will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <div class="filter-section">
                    <label>Symbol: </label>
                    <select id="symbolFilter">
                        <option value="">All Symbols</option>
                    </select>
                    
                    <label>Status: </label>
                    <select id="statusFilter">
                        <option value="">All Status</option>
                        <option value="NEW">New</option>
                        <option value="FILLED">Filled</option>
                        <option value="CANCELED">Canceled</option>
                        <option value="PARTIALLY_FILLED">Partially Filled</option>
                    </select>
                    
                    <label>Side: </label>
                    <select id="sideFilter">
                        <option value="">All</option>
                        <option value="BUY">Buy</option>
                        <option value="SELL">Sell</option>
                    </select>
                    
                    <button class="refresh-btn" onclick="refreshOrders()">🔄 Refresh</button>
                </div>
                
                <h2>Open Orders</h2>
                <div id="openOrdersContainer">
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Type</th>
                                <th>Quantity</th>
                                <th>Price</th>
                                <th>Filled</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="openOrdersBody">
                            <!-- Orders will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card">
                <h2>Recent Order History</h2>
                <div id="orderHistoryContainer">
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Type</th>
                                <th>Quantity</th>
                                <th>Price</th>
                                <th>Filled</th>
                                <th>Status</th>
                                <th>P&L</th>
                            </tr>
                        </thead>
                        <tbody id="orderHistoryBody">
                            <!-- Order history will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            async function fetchOpenOrders() {
                try {
                    const response = await fetch('/api/orders/open');
                    const data = await response.json();
                    updateOpenOrders(data);
                } catch (error) {
                    console.error('Error fetching open orders:', error);
                    document.getElementById('openOrdersBody').innerHTML = 
                        '<tr><td colspan="9" style="text-align: center; color: #999;">Error loading orders</td></tr>';
                }
            }
            
            async function fetchOrderHistory() {
                try {
                    const response = await fetch('/api/orders/history?limit=50');
                    const data = await response.json();
                    updateOrderHistory(data);
                } catch (error) {
                    console.error('Error fetching order history:', error);
                    document.getElementById('orderHistoryBody').innerHTML = 
                        '<tr><td colspan="9" style="text-align: center; color: #999;">Error loading history</td></tr>';
                }
            }
            
            async function fetchOrderSummary() {
                try {
                    const response = await fetch('/api/orders/summary');
                    const data = await response.json();
                    updateSummary(data);
                } catch (error) {
                    console.error('Error fetching summary:', error);
                }
            }
            
            function updateOpenOrders(orders) {
                const tbody = document.getElementById('openOrdersBody');
                if (!orders || orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #999;">No open orders</td></tr>';
                    return;
                }
                
                tbody.innerHTML = orders.map(order => `
                    <tr>
                        <td>${new Date(order.time).toLocaleString()}</td>
                        <td>${order.symbol}</td>
                        <td class="side-${order.side.toLowerCase()}">${order.side}</td>
                        <td>${order.type}</td>
                        <td>${parseFloat(order.quantity).toFixed(6)}</td>
                        <td>${order.price ? parseFloat(order.price).toFixed(6) : 'Market'}</td>
                        <td>${parseFloat(order.executedQty || 0).toFixed(6)}</td>
                        <td><span class="status-${order.status.toLowerCase().replace('_', '-')}">${order.status}</span></td>
                        <td>
                            <button onclick="cancelOrder('${order.symbol}', '${order.orderId}')" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">Cancel</button>
                        </td>
                    </tr>
                `).join('');
            }
            
            function updateOrderHistory(orders) {
                const tbody = document.getElementById('orderHistoryBody');
                if (!orders || orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #999;">No order history</td></tr>';
                    return;
                }
                
                tbody.innerHTML = orders.map(order => `
                    <tr>
                        <td>${new Date(order.time).toLocaleString()}</td>
                        <td>${order.symbol}</td>
                        <td class="side-${order.side.toLowerCase()}">${order.side}</td>
                        <td>${order.type}</td>
                        <td>${parseFloat(order.quantity).toFixed(6)}</td>
                        <td>${order.price ? parseFloat(order.price).toFixed(6) : 'Market'}</td>
                        <td>${parseFloat(order.executedQty || 0).toFixed(6)}</td>
                        <td><span class="status-${order.status.toLowerCase().replace('_', '-')}">${order.status}</span></td>
                        <td style="color: ${(order.pnl || 0) >= 0 ? '#2e7d32' : '#c62828'}">${order.pnl ? (order.pnl >= 0 ? '+' : '') + order.pnl.toFixed(2) : 'N/A'}</td>
                    </tr>
                `).join('');
            }
            
            function updateSummary(summary) {
                const summaryDiv = document.getElementById('summary');
                summaryDiv.innerHTML = `
                    <div class="summary-item">
                        <h4>Open Orders</h4>
                        <p>${summary.open_orders || 0}</p>
                    </div>
                    <div class="summary-item">
                        <h4>Today's Trades</h4>
                        <p>${summary.todays_trades || 0}</p>
                    </div>
                    <div class="summary-item">
                        <h4>Total Volume</h4>
                        <p>$${(summary.total_volume || 0).toFixed(2)}</p>
                    </div>
                    <div class="summary-item">
                        <h4>Success Rate</h4>
                        <p>${(summary.success_rate || 0).toFixed(1)}%</p>
                    </div>
                    <div class="summary-item">
                        <h4>Avg. Trade Size</h4>
                        <p>$${(summary.avg_trade_size || 0).toFixed(2)}</p>
                    </div>
                `;
            }
            
            async function cancelOrder(symbol, orderId) {
                if (!confirm(`Are you sure you want to cancel order ${orderId}?`)) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/orders/cancel`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol: symbol, order_id: orderId })
                    });
                    
                    if (response.ok) {
                        alert('Order canceled successfully');
                        refreshOrders();
                    } else {
                        alert('Failed to cancel order');
                    }
                } catch (error) {
                    console.error('Error canceling order:', error);
                    alert('Error canceling order');
                }
            }
            
            function refreshOrders() {
                fetchOpenOrders();
                fetchOrderHistory();
                fetchOrderSummary();
            }
            
            // Initial load
            document.addEventListener('DOMContentLoaded', function() {
                refreshOrders();
                
                // Auto-refresh every 10 seconds
                setInterval(refreshOrders, 10000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/orders/open")
async def get_open_orders():
    """Get all open orders"""
    try:
        orders = binance_client.get_open_orders()
        return orders if orders else []
    except Exception as e:
        logger.error(f"Error getting open orders: {e}")
        return []


@app.get("/api/orders/history")
async def get_order_history(limit: int = 50):
    """Get order history"""
    try:
        # 您可以從資料庫或者 Binance API 獲取歷史訂單
        # 這裡先返回一個示例
        return []
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        return []


@app.get("/api/orders/summary")
async def get_orders_summary():
    """Get orders summary statistics"""
    try:
        open_orders = binance_client.get_open_orders()
        
        summary = {
            "open_orders": len(open_orders) if open_orders else 0,
            "todays_trades": 0,  # 從資料庫計算
            "total_volume": 0.0,  # 從資料庫計算
            "success_rate": 0.0,  # 從資料庫計算
            "avg_trade_size": 0.0  # 從資料庫計算
        }
        
        return summary
    except Exception as e:
        logger.error(f"Error getting orders summary: {e}")
        return {
            "open_orders": 0,
            "todays_trades": 0,
            "total_volume": 0.0,
            "success_rate": 0.0,
            "avg_trade_size": 0.0
        }


@app.post("/api/orders/cancel")
async def cancel_order(request: Dict[str, str]):
    """Cancel an order"""
    try:
        symbol = request.get("symbol")
        order_id = request.get("order_id")
        
        if not symbol or not order_id:
            raise HTTPException(status_code=400, detail="Symbol and order_id are required")
        
        result = binance_client.cancel_order(symbol, order_id)
        return {"message": "Order canceled successfully", "result": result}
    except Exception as e:
        logger.error(f"Error canceling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions", response_class=HTMLResponse)
async def positions_page():
    """Positions monitoring page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Bot - Positions</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav { background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px; }
            .nav a { color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .nav a.active { background: #007bff; }
            .balances-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .balance-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
            .balance-card h4 { margin: 0 0 8px 0; color: #495057; }
            .balance-card .amount { font-size: 18px; font-weight: bold; color: #212529; }
            .balance-card .value { font-size: 14px; color: #6c757d; }
            .refresh-btn { background: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin: 10px 0; }
            .refresh-btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/orders">Orders</a>
                <a href="/positions" class="active">Positions</a>
                <a href="/history">History</a>
            </div>
              <h1>💰 Portfolio & Positions</h1>
            
            <div class="card">
                <h2>Portfolio Summary</h2>
                <div class="stats-grid" id="portfolioStats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <!-- Portfolio stats will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <button class="refresh-btn" onclick="refreshBalances()">🔄 Refresh Balances</button>
                <h2>Account Balances</h2>
                <div class="balances-grid" id="balancesGrid">
                    <!-- Balances will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Open Positions</h2>
                <div id="openPositions">
                    <!-- Open positions will be populated by JavaScript -->
                </div>
            </div>
        </div>
          <script>
            async function fetchBalances() {
                try {
                    const response = await fetch('/api/account/balances');
                    const data = await response.json();
                    updateBalances(data);
                    updatePortfolioStats(data);
                } catch (error) {
                    console.error('Error fetching balances:', error);
                    document.getElementById('balancesGrid').innerHTML = 
                        '<div style="grid-column: 1 / -1; text-align: center; color: #999;">Error loading balances</div>';
                }
            }
            
            async function fetchOpenPositions() {
                try {
                    const response = await fetch('/api/trading/positions');
                    const data = await response.json();
                    updateOpenPositions(data);
                } catch (error) {
                    console.error('Error fetching positions:', error);
                    document.getElementById('openPositions').innerHTML = 
                        '<div style="text-align: center; color: #999;">Error loading positions</div>';
                }
            }
            
            function updatePortfolioStats(balances) {
                const stats = document.getElementById('portfolioStats');
                
                let totalAssets = 0;
                let totalValue = 0; // 假設 USDT 價值
                let lockedAssets = 0;
                
                Object.entries(balances).forEach(([asset, balance]) => {
                    totalAssets++;
                    if (asset === 'USDT') {
                        totalValue += balance.total || 0;
                    }
                    if (balance.locked > 0) {
                        lockedAssets++;
                    }
                });
                
                stats.innerHTML = `
                    <div class="balance-card">
                        <h4>Total Assets</h4>
                        <div class="amount">${totalAssets}</div>
                    </div>
                    <div class="balance-card">
                        <h4>Portfolio Value</h4>
                        <div class="amount">≈ $${totalValue.toFixed(2)}</div>
                    </div>
                    <div class="balance-card">
                        <h4>Assets with Orders</h4>
                        <div class="amount">${lockedAssets}</div>
                    </div>
                `;
            }
            
            function updateBalances(balances) {
                const grid = document.getElementById('balancesGrid');
                
                if (!balances || Object.keys(balances).length === 0) {
                    grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: #999;">No balances found</div>';
                    return;
                }
                
                // 過濾出有餘額的資產
                const nonZeroBalances = Object.entries(balances).filter(([asset, balance]) => balance.total > 0);
                
                if (nonZeroBalances.length === 0) {
                    grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: #999;">All balances are zero</div>';
                    return;
                }
                
                grid.innerHTML = nonZeroBalances.map(([asset, balance]) => {
                    const total = balance.total || 0;
                    const free = balance.free || 0;
                    const locked = balance.locked || 0;
                    const utilization = total > 0 ? ((locked / total) * 100).toFixed(1) : 0;
                    
                    return `
                        <div class="balance-card" style="border-left: 4px solid ${locked > 0 ? '#ffc107' : '#28a745'};">
                            <h4>${asset}</h4>
                            <div class="amount">${total.toFixed(8)}</div>
                            <div class="value">Free: ${free.toFixed(8)}</div>
                            <div class="value">Locked: ${locked.toFixed(8)}</div>
                            <div class="value" style="color: ${locked > 0 ? '#ffc107' : '#6c757d'};">
                                ${locked > 0 ? `${utilization}% in orders` : 'Available'}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function updateOpenPositions(positions) {
                const container = document.getElementById('openPositions');
                
                if (!positions || positions.length === 0) {
                    container.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">No open positions</div>';
                    return;
                }
                
                container.innerHTML = `
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid #dee2e6;">
                                <th style="padding: 8px; text-align: left;">Symbol</th>
                                <th style="padding: 8px; text-align: left;">Side</th>
                                <th style="padding: 8px; text-align: left;">Size</th>
                                <th style="padding: 8px; text-align: left;">Entry Price</th>
                                <th style="padding: 8px; text-align: left;">Current Price</th>
                                <th style="padding: 8px; text-align: left;">P&L</th>
                                <th style="padding: 8px; text-align: left;">P&L %</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${positions.map(pos => `
                                <tr style="border-bottom: 1px solid #dee2e6;">
                                    <td style="padding: 8px;">${pos.symbol}</td>
                                    <td style="padding: 8px; color: ${pos.side === 'BUY' ? '#28a745' : '#dc3545'};">${pos.side}</td>
                                    <td style="padding: 8px;">${pos.size}</td>
                                    <td style="padding: 8px;">$${pos.entry_price}</td>
                                    <td style="padding: 8px;">$${pos.current_price}</td>
                                    <td style="padding: 8px; color: ${pos.pnl >= 0 ? '#28a745' : '#dc3545'};">$${pos.pnl.toFixed(2)}</td>
                                    <td style="padding: 8px; color: ${pos.pnl_percent >= 0 ? '#28a745' : '#dc3545'};">${pos.pnl_percent.toFixed(2)}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            function refreshBalances() {
                fetchBalances();
                fetchOpenPositions();
            }
            
            // Initial load
            document.addEventListener('DOMContentLoaded', function() {
                refreshBalances();
                
                // Auto-refresh every 30 seconds
                setInterval(refreshBalances, 30000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/account/balances")
async def get_account_balances():
    """Get account balances"""
    try:
        balances = binance_client.get_balance()
        return balances if balances else {}
    except Exception as e:
        logger.error(f"Error getting balances: {e}")
        return {}


@app.get("/history", response_class=HTMLResponse)
async def history_page():
    """Trading history page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Bot - Trading History</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav { background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px; }
            .nav a { color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .nav a.active { background: #007bff; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .stat-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
            .stat-card h4 { margin: 0 0 8px 0; color: #495057; }
            .stat-card .value { font-size: 20px; font-weight: bold; }
            .profit { color: #28a745; }
            .loss { color: #dc3545; }
            .neutral { color: #6c757d; }
            .history-table { width: 100%; border-collapse: collapse; font-size: 14px; }
            .history-table th, .history-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            .history-table th { background-color: #f8f9fa; font-weight: bold; }
            .history-table tr:hover { background-color: #f5f5f5; }
            .filter-section { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px; }
            .filter-section select, .filter-section input { margin: 5px; padding: 5px; border: 1px solid #ddd; border-radius: 3px; }
            .refresh-btn { background: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin: 10px 0; }
            .refresh-btn:hover { background: #0056b3; }
            .chart-container { height: 400px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/orders">Orders</a>
                <a href="/positions">Positions</a>
                <a href="/history" class="active">History</a>
            </div>
            
            <h1>📈 Trading History</h1>
            
            <div class="card">
                <h2>Performance Statistics</h2>
                <div class="stats-grid" id="statsGrid">
                    <!-- Stats will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>P&L Chart</h2>
                <div class="chart-container">
                    <canvas id="pnlChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="filter-section">
                    <label>Date Range: </label>
                    <input type="date" id="startDate">
                    <input type="date" id="endDate">
                    
                    <label>Symbol: </label>
                    <select id="symbolFilter">
                        <option value="">All Symbols</option>
                    </select>
                    
                    <label>Result: </label>
                    <select id="resultFilter">
                        <option value="">All</option>
                        <option value="profit">Profit</option>
                        <option value="loss">Loss</option>
                    </select>
                    
                    <button class="refresh-btn" onclick="refreshHistory()">🔄 Refresh</button>
                    <button class="refresh-btn" onclick="exportData()" style="background: #28a745;">📊 Export CSV</button>
                </div>
                
                <h2>Trade History</h2>
                <div id="historyContainer">
                    <table class="history-table">
                        <thead>
                            <tr>
                                <th>Date & Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>Quantity</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                                <th>Duration</th>
                                <th>Strategy</th>
                            </tr>
                        </thead>
                        <tbody id="historyBody">
                            <!-- Trade history will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            let pnlChart = null;
            
            async function fetchTradingStats() {
                try {
                    const response = await fetch('/api/trading/stats');
                    const data = await response.json();
                    updateStats(data);
                } catch (error) {
                    console.error('Error fetching trading stats:', error);
                }
            }
            
            async function fetchTradingHistory() {
                try {
                    const params = new URLSearchParams();
                    const startDate = document.getElementById('startDate').value;
                    const endDate = document.getElementById('endDate').value;
                    const symbol = document.getElementById('symbolFilter').value;
                    const result = document.getElementById('resultFilter').value;
                    
                    if (startDate) params.append('start_date', startDate);
                    if (endDate) params.append('end_date', endDate);
                    if (symbol) params.append('symbol', symbol);
                    if (result) params.append('result', result);
                    
                    const response = await fetch(`/api/trading/history?${params}`);
                    const data = await response.json();
                    updateHistory(data);
                } catch (error) {
                    console.error('Error fetching trading history:', error);
                    document.getElementById('historyBody').innerHTML = 
                        '<tr><td colspan="10" style="text-align: center; color: #999;">Error loading history</td></tr>';
                }
            }
            
            async function fetchPnLData() {
                try {
                    const response = await fetch('/api/trading/pnl-chart');
                    const data = await response.json();
                    updatePnLChart(data);
                } catch (error) {
                    console.error('Error fetching P&L data:', error);
                }
            }
            
            function updateStats(stats) {
                const grid = document.getElementById('statsGrid');
                grid.innerHTML = `
                    <div class="stat-card">
                        <h4>Total Trades</h4>
                        <div class="value neutral">${stats.total_trades || 0}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Winning Trades</h4>
                        <div class="value profit">${stats.winning_trades || 0}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Losing Trades</h4>
                        <div class="value loss">${stats.losing_trades || 0}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Win Rate</h4>
                        <div class="value ${stats.win_rate >= 50 ? 'profit' : 'loss'}">${(stats.win_rate || 0).toFixed(1)}%</div>
                    </div>
                    <div class="stat-card">
                        <h4>Total P&L</h4>
                        <div class="value ${(stats.total_pnl || 0) >= 0 ? 'profit' : 'loss'}">$${(stats.total_pnl || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Best Trade</h4>
                        <div class="value profit">$${(stats.best_trade || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Worst Trade</h4>
                        <div class="value loss">$${(stats.worst_trade || 0).toFixed(2)}</div>
                    </div>
                    <div class="stat-card">
                        <h4>Avg. Trade</h4>
                        <div class="value ${(stats.avg_trade || 0) >= 0 ? 'profit' : 'loss'}">$${(stats.avg_trade || 0).toFixed(2)}</div>
                    </div>
                `;
            }
            
            function updateHistory(trades) {
                const tbody = document.getElementById('historyBody');
                if (!trades || trades.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #999;">No trading history found</td></tr>';
                    return;
                }
                
                tbody.innerHTML = trades.map(trade => {
                    const pnl = trade.pnl || 0;
                    const pnlPercent = trade.pnl_percent || 0;
                    const pnlClass = pnl >= 0 ? 'profit' : 'loss';
                    
                    return `
                        <tr>
                            <td>${new Date(trade.entry_time).toLocaleString()}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.side}</td>
                            <td>$${(trade.entry_price || 0).toFixed(6)}</td>
                            <td>$${(trade.exit_price || 0).toFixed(6)}</td>
                            <td>${(trade.quantity || 0).toFixed(6)}</td>
                            <td class="${pnlClass}">$${pnl.toFixed(2)}</td>
                            <td class="${pnlClass}">${pnlPercent.toFixed(2)}%</td>
                            <td>${trade.duration || 'N/A'}</td>
                            <td>${trade.strategy || 'N/A'}</td>
                        </tr>
                    `;
                }).join('');
            }
            
            function updatePnLChart(data) {
                const ctx = document.getElementById('pnlChart').getContext('2d');
                
                if (pnlChart) {
                    pnlChart.destroy();
                }
                
                pnlChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.labels || [],
                        datasets: [{
                            label: 'Cumulative P&L',
                            data: data.values || [],
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)',
                            tension: 0.1,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'P&L ($)'
                                }
                            },
                            x: {
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                display: true
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false
                            }
                        }
                    }
                });
            }
            
            function exportData() {
                // 這裡可以實現數據導出功能
                alert('Export functionality will be implemented');
            }
            
            function refreshHistory() {
                fetchTradingStats();
                fetchTradingHistory();
                fetchPnLData();
            }
            
            // Set default date range (last 30 days)
            function setDefaultDates() {
                const endDate = new Date();
                const startDate = new Date();
                startDate.setDate(endDate.getDate() - 30);
                
                document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
                document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
            }
            
            // Initial load
            document.addEventListener('DOMContentLoaded', function() {
                setDefaultDates();
                refreshHistory();
                
                // Auto-refresh every 60 seconds
                setInterval(refreshHistory, 60000);
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/trading/history")
async def get_trading_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 100
):
    """Get trading history with filters"""
    try:
        # 這裡應該從資料庫獲取真實的交易歷史
        # 暫時返回示例數據
        sample_trades = [
            {
                "entry_time": "2025-06-15T10:30:00Z",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "entry_price": 42500.00,
                "exit_price": 43100.00,
                "quantity": 0.001,
                "pnl": 0.60,
                "pnl_percent": 1.41,
                "duration": "2h 15m",
                "strategy": "MA Cross"
            },
            {
                "entry_time": "2025-06-15T08:15:00Z",
                "symbol": "ETHUSDT",
                "side": "BUY",
                "entry_price": 2450.00,
                "exit_price": 2420.00,
                "quantity": 0.01,
                "pnl": -0.30,
                "pnl_percent": -1.22,
                "duration": "1h 45m",
                "strategy": "MA Cross"
            }
        ]
        
        # 應用過濾器
        filtered_trades = sample_trades
        if symbol:
            filtered_trades = [t for t in filtered_trades if t["symbol"] == symbol]
        if result == "profit":
            filtered_trades = [t for t in filtered_trades if t["pnl"] > 0]
        elif result == "loss":
            filtered_trades = [t for t in filtered_trades if t["pnl"] < 0]
            
        return filtered_trades[:limit]
    except Exception as e:
        logger.error(f"Error getting trading history: {e}")
        return []


@app.get("/api/trading/stats")
async def get_trading_stats():
    """Get trading statistics"""
    try:
        # 這裡應該從資料庫獲取真實的交易統計
        # 暫時返回示例數據
        stats = {
            "total_trades": 25,
            "winning_trades": 18,
            "losing_trades": 7,
            "win_rate": 72.0,
            "total_pnl": 1250.75,
            "best_trade": 185.50,
            "worst_trade": -95.25,
            "avg_trade": 50.03
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting trading stats: {e}")
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "avg_trade": 0.0
        }


@app.get("/api/trading/pnl-chart")
async def get_pnl_chart_data():
    """Get P&L chart data"""
    try:
        # 這裡應該從資料庫獲取真實的 P&L 數據
        # 暫時返回示例數據
        from datetime import datetime, timedelta
        
        base_date = datetime.now() - timedelta(days=30)
        labels = [];
        values = [];
        cumulative_pnl = 10000.0  # 起始金額
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            labels.append(date.strftime("%m-%d"));
            
            # 模擬隨機 P&L 變化
            import random
            daily_change = random.uniform(-50, 100);
            cumulative_pnl += daily_change;
            values.append(round(cumulative_pnl, 2));
        
        return {
            "labels": labels,
            "values": values
        }
    except Exception as e:
        logger.error(f"Error getting P&L chart data: {e}")
        return {
            "labels": [],
            "values": []
        }


@app.get("/api/debug/status")
async def debug_status():
    """Debug status endpoint with detailed information"""
    try:
        debug_info = {
            "trading_engine_exists": trading_engine is not None,
            "trading_engine_is_running": trading_engine.is_running if trading_engine else False,
            "trading_engine_session_id": trading_engine.session_id if trading_engine else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if trading_engine:
            try:
                status = trading_engine.get_status()
                debug_info["status_call_success"] = True
                debug_info["status_data"] = status
            except Exception as e:
                debug_info["status_call_success"] = False
                debug_info["status_error"] = str(e)
        
        return debug_info
    except Exception as e:
        logger.error(f"Error in debug status: {e}")
        return {"error": str(e)}


@app.post("/api/debug/test-start")
async def debug_test_start():
    """Test trading engine creation without background task"""
    try:
        global trading_engine
        
        logger.info("Debug: Creating new trading engine...")
        trading_engine = TradingEngine("ma_cross")
        
        logger.info("Debug: Setting is_running to True...")
        trading_engine.is_running = True
        trading_engine.session_id = f"debug_session_{int(datetime.utcnow().timestamp())}"
        
        logger.info("Debug: Testing get_status...")
        status = trading_engine.get_status()
        
        return {
            "message": "Debug start completed",
            "trading_engine_created": True,
            "is_running": trading_engine.is_running,
            "session_id": trading_engine.session_id,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error in debug test start: {e}")
        return {"error": str(e)}


@app.get("/api/trading/positions")
async def get_trading_positions():
    """Get current trading positions"""
    try:
        # 這裡應該從資料庫或交易引擎獲取實際的持倉
        # 目前返回示例數據
        positions = [
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "size": "0.001",
                "entry_price": "42500.00",
                "current_price": "43100.00",
                "pnl": 0.60,
                "pnl_percent": 1.41
            }
        ]
        return positions
    except Exception as e:
        logger.error(f"Error getting trading positions: {e}")
        return []


# ==================== 合約交易 API ====================

@app.get("/futures", response_class=HTMLResponse)
async def futures_page():
    """Futures trading page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Bot - Futures Trading</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .nav { background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px; }
            .nav a { color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; }
            .nav a:hover { background: #555; }
            .nav a.active { background: #007bff; }
            .position-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .position-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
            .position-card.long { border-left-color: #28a745; }
            .position-card.short { border-left-color: #dc3545; }
            .profit { color: #28a745; }
            .loss { color: #dc3545; }
            .leverage-controls { margin: 15px 0; }
            .leverage-controls select, .leverage-controls button { margin: 5px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { background: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/">Dashboard</a>
                <a href="/orders">Orders</a>
                <a href="/positions">Spot Positions</a>
                <a href="/futures" class="active">Futures</a>
                <a href="/history">History</a>
            </div>
            
            <h1>⚡ Futures Trading</h1>
            
            <div class="card">
                <h2>Futures Account Summary</h2>
                <div id="futuresAccountSummary">
                    <!-- Account summary will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Open Positions</h2>
                <button class="btn" onclick="refreshPositions()">🔄 Refresh Positions</button>
                <div class="position-grid" id="futuresPositions">
                    <!-- Positions will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <div class="leverage-controls">
                    <label>Symbol: </label>
                    <select id="symbolSelect">
                        <option value="BTCUSDT">BTCUSDT</option>
                        <option value="ETHUSDT">ETHUSDT</option>
                        <option value="ADAUSDT">ADAUSDT</option>
                    </select>
                    
                    <label>Leverage: </label>
                    <select id="leverageSelect">
                        <option value="5">5x</option>
                        <option value="10" selected>10x</option>
                        <option value="20">20x</option>
                    </select>
                    
                    <button class="btn" onclick="changeLeverage()">Set Leverage</button>
                </div>
                
                <div>
                    <button class="btn btn-success" onclick="openLongPosition()">📈 Open Long</button>
                    <button class="btn btn-danger" onclick="openShortPosition()">📉 Open Short</button>
                    <button class="btn btn-danger" onclick="closeAllPositions()">❌ Close All Positions</button>
                </div>
            </div>
        </div>
        
        <script>
            async function refreshPositions() {
                try {
                    const response = await fetch('/api/futures/positions');
                    const positions = await response.json();
                    updatePositions(positions);
                    
                    const balanceResponse = await fetch('/api/futures/balance');
                    const balance = await balanceResponse.json();
                    updateAccountSummary(balance);
                } catch (error) {
                    console.error('Error refreshing positions:', error);
                }
            }
            
            function updatePositions(positions) {
                const container = document.getElementById('futuresPositions');
                
                if (!positions || positions.length === 0) {
                    container.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: #999; padding: 20px;">No open positions</div>';
                    return;
                }
                
                container.innerHTML = positions.map(pos => {
                    const isLong = pos.position_amt > 0;
                    const pnlClass = pos.unrealized_pnl >= 0 ? 'profit' : 'loss';
                    const positionClass = isLong ? 'long' : 'short';
                    
                    return `
                        <div class="position-card ${positionClass}">
                            <h4>${pos.symbol} ${isLong ? 'LONG' : 'SHORT'}</h4>
                            <p><strong>Size:</strong> ${Math.abs(pos.position_amt)}</p>
                            <p><strong>Entry Price:</strong> $${pos.entry_price}</p>
                            <p><strong>Mark Price:</strong> $${pos.mark_price}</p>
                            <p><strong>P&L:</strong> <span class="${pnlClass}">$${pos.unrealized_pnl.toFixed(2)} (${pos.percentage.toFixed(2)}%)</span></p>
                            <p><strong>Notional:</strong> $${pos.notional.toFixed(2)}</p>
                            <button class="btn btn-danger" onclick="closePosition('${pos.symbol}')">Close Position</button>
                        </div>
                    `;
                }).join('');
            }
            
            function updateAccountSummary(balance) {
                const container = document.getElementById('futuresAccountSummary');
                
                if (!balance.USDT) {
                    container.innerHTML = '<p style="color: #999;">No futures account data available</p>';
                    return;
                }
                
                const usdt = balance.USDT;
                container.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                            <h4>Wallet Balance</h4>
                            <div style="font-size: 18px; font-weight: bold;">${usdt.wallet_balance.toFixed(2)} USDT</div>
                        </div>
                        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                            <h4>Available Balance</h4>
                            <div style="font-size: 18px; font-weight: bold;">${usdt.available_balance.toFixed(2)} USDT</div>
                        </div>
                        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                            <h4>Unrealized P&L</h4>
                            <div style="font-size: 18px; font-weight: bold; color: ${usdt.unrealized_pnl >= 0 ? '#28a745' : '#dc3545'};">${usdt.unrealized_pnl.toFixed(2)} USDT</div>
                        </div>
                        <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 6px;">
                            <h4>Margin Balance</h4>
                            <div style="font-size: 18px; font-weight: bold;">${usdt.margin_balance.toFixed(2)} USDT</div>
                        </div>
                    </div>
                `;
            }
            
            async function changeLeverage() {
                const symbol = document.getElementById('symbolSelect').value;
                const leverage = document.getElementById('leverageSelect').value;
                
                try {
                    const response = await fetch('/api/futures/leverage', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol, leverage: parseInt(leverage) })
                    });
                    
                    if (response.ok) {
                        alert(`Leverage set to ${leverage}x for ${symbol}`);
                    } else {
                        alert('Failed to set leverage');
                    }
                } catch (error) {
                    console.error('Error setting leverage:', error);
                    alert('Error setting leverage');
                }
            }
            
            async function closePosition(symbol) {
                if (!confirm(`Close position for ${symbol}?`)) return;
                
                try {
                    const response = await fetch('/api/futures/close-position', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol })
                    });
                    
                    if (response.ok) {
                        alert(`Position closed for ${symbol}`);
                        refreshPositions();
                    } else {
                        alert('Failed to close position');
                    }
                } catch (error) {
                    console.error('Error closing position:', error);
                    alert('Error closing position');
                }
            }
            
            // Load data on page load
            refreshPositions();
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/futures/account")
async def get_futures_account():
    """Get futures account information"""
    try:
        account = binance_client.get_futures_account()
        return account
    except Exception as e:
        logger.error(f"Error getting futures account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/futures/balance")
async def get_futures_balance():
    """Get futures account balance"""
    try:
        balance = binance_client.get_futures_balance()
        return balance
    except Exception as e:
        logger.error(f"Error getting futures balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/futures/positions")
async def get_futures_positions():
    """Get futures positions"""
    try:
        positions = binance_client.get_futures_positions()
        return positions
    except Exception as e:
        logger.error(f"Error getting futures positions: {e}")
        return []


@app.post("/api/futures/leverage")
async def change_futures_leverage(request: dict):
    """Change leverage for a futures symbol"""
    try:
        symbol = request.get('symbol')
        leverage = request.get('leverage')
        
        if not symbol or not leverage:
            raise HTTPException(status_code=400, detail="Symbol and leverage are required")
        
        result = binance_client.change_futures_leverage(symbol, leverage)
        return {"message": "Leverage changed successfully", "result": result}
    except Exception as e:
        logger.error(f"Error changing leverage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/futures/order")
async def place_futures_order(request: dict):
    """Place a futures order"""
    try:
        symbol = request.get('symbol')
        side = request.get('side')
        order_type = request.get('type', 'MARKET')
        quantity = request.get('quantity')
        price = request.get('price')
        position_side = request.get('positionSide', 'BOTH')
        
        if not symbol or not side or not quantity:
            raise HTTPException(status_code=400, detail="Symbol, side, and quantity are required")
        
        result = binance_client.place_futures_order(
            symbol=str(symbol),
            side=str(side),
            order_type=str(order_type),
            quantity=float(quantity),
            price=float(price) if price else None,
            position_side=str(position_side)
        )
        
        return {"message": "Futures order placed successfully", "result": result}
    except Exception as e:
        logger.error(f"Error placing futures order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/futures/close-position")
async def close_futures_position(request: dict):
    """Close a futures position"""
    try:
        symbol = request.get('symbol')
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # 獲取當前持倉
        positions = binance_client.get_futures_positions(symbol)
        if not positions:
            raise HTTPException(status_code=404, detail="No position found for this symbol")
        
        position = positions[0]
        position_amt = position['position_amt']
        
        if position_amt == 0:
            raise HTTPException(status_code=400, detail="No position to close")
        
        # 平倉：反向操作
        side = 'SELL' if position_amt > 0 else 'BUY'
        quantity = abs(position_amt)
        
        result = binance_client.place_futures_order(
            symbol=symbol,
            side=side,
            order_type='MARKET',
            quantity=quantity,
            reduce_only=True
        )
        
        return {"message": "Position closed successfully", "result": result}
    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_api_server(host="0.0.0.0", port=8000):
    """啟動 FastAPI 伺服器"""
    import uvicorn
    uvicorn.run("src.api:app", host=host, port=port, reload=True)
