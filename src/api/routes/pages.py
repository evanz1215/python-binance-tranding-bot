"""
HTML pages routes
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

def get_dashboard_html():
    """Get dashboard HTML content"""
    return """
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
        </style>
    </head>
    <body>
        <div class="container">
            <div style="background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px;">
                <a href="/" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; background: #007bff;">Dashboard</a>
                <a href="/orders" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Orders</a>
                <a href="/positions" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Positions</a>
                <a href="/history" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">History</a>
            </div>
            
            <h1>🤖 Binance Trading Bot Dashboard</h1>
            
            <div class="card">
                <h2>Trading Status</h2>
                <div class="status" id="status-grid">
                    <div class="metric">
                        <h3>Status</h3>
                        <p id="bot-status" class="stopped">Loading...</p>
                    </div>
                    <div class="metric">
                        <h3>Strategy</h3>
                        <p id="strategy">Loading...</p>
                    </div>
                    <div class="metric">
                        <h3>Positions</h3>
                        <p id="positions">Loading...</p>
                    </div>
                    <div class="metric">
                        <h3>Risk Level</h3>
                        <p id="risk-level" class="risk-low">Loading...</p>
                    </div>
                    <div class="metric">
                        <h3>Balance</h3>
                        <p id="balance">Loading...</p>
                    </div>
                    <div class="metric">
                        <h3>Daily P&L</h3>
                        <p id="daily-pnl">Loading...</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Controls</h2>
                <button class="btn-success" onclick="startTrading()">Start Trading</button>
                <button class="btn-danger" onclick="stopTrading()">Stop Trading</button>
                <button class="btn-primary" onclick="refreshData()">Refresh</button>
            </div>
        </div>
        
        <script>
            async function fetchStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    document.getElementById('bot-status').textContent = data.is_running ? 'Running' : 'Stopped';
                    document.getElementById('bot-status').className = data.is_running ? 'running' : 'stopped';
                    document.getElementById('strategy').textContent = data.strategy;
                    document.getElementById('positions').textContent = data.active_positions;
                    document.getElementById('risk-level').textContent = data.risk_level;
                    document.getElementById('balance').textContent = '$' + data.total_balance.toFixed(2);
                    document.getElementById('daily-pnl').textContent = '$' + data.daily_pnl.toFixed(2);
                } catch (error) {
                    console.error('Error fetching status:', error);
                }
            }
            
            async function startTrading() {
                try {
                    const response = await fetch('/api/trading/start', { method: 'POST' });
                    const data = await response.json();
                    alert(data.message);
                    fetchStatus();
                } catch (error) {
                    alert('Error starting trading: ' + error.message);
                }
            }
            
            async function stopTrading() {
                try {
                    const response = await fetch('/api/trading/stop', { method: 'POST' });
                    const data = await response.json();
                    alert(data.message);
                    fetchStatus();
                } catch (error) {
                    alert('Error stopping trading: ' + error.message);
                }
            }
            
            function refreshData() {
                fetchStatus();
            }
            
            // Auto refresh every 30 seconds
            setInterval(fetchStatus, 30000);
            
            // Initial load
            fetchStatus();
        </script>
    </body>
    </html>
    """

@router.get("/orders", response_class=HTMLResponse)
async def orders_page():
    """Orders page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orders - Binance Trading Bot</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            .status-filled { color: #28a745; font-weight: bold; }
            .status-canceled { color: #dc3545; }
            .side-buy { color: #28a745; font-weight: bold; }
            .side-sell { color: #dc3545; font-weight: bold; }
            .trading-mode { background: #e9ecef; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }
            .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .summary-item { background: #007bff; color: white; padding: 15px; border-radius: 8px; text-align: center; }
            .summary-item h3 { margin: 0; font-size: 1.5em; }
            .summary-item p { margin: 5px 0 0 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px;">
                <a href="/" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Dashboard</a>
                <a href="/orders" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; background: #007bff;">Orders</a>
                <a href="/positions" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Positions</a>
                <a href="/history" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">History</a>
            </div>
            
            <h1>📋 訂單管理</h1>
            
            <!-- 訂單摘要 -->
            <div class="card">
                <h2>訂單摘要</h2>
                <div class="summary" id="summary-container">
                    <div class="summary-item">
                        <h3 id="open-orders-count">-</h3>
                        <p>未完成訂單</p>
                    </div>
                    <div class="summary-item">
                        <h3 id="today-trades">-</h3>
                        <p>今日交易</p>
                    </div>
                    <div class="summary-item">
                        <h3 id="total-volume">-</h3>
                        <p>總交易量 (USDT)</p>
                    </div>
                    <div class="summary-item">
                        <h3 id="trading-mode">-</h3>
                        <p>交易模式</p>
                    </div>
                </div>
            </div>
            
            <!-- 未完成訂單 -->
            <div class="card">
                <h2>未完成訂單</h2>
                <table id="open-orders-table">
                    <thead>
                        <tr>
                            <th>訂單ID</th>
                            <th>交易對</th>
                            <th>方向</th>
                            <th>類型</th>
                            <th>數量</th>
                            <th>價格</th>
                            <th>狀態</th>
                            <th>時間</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="open-orders-body">
                        <tr><td colspan="9">載入中...</td></tr>
                    </tbody>
                </table>
            </div>
            
            <!-- 訂單歷史 -->
            <div class="card">
                <h2>訂單歷史</h2>
                <table id="history-orders-table">
                    <thead>
                        <tr>
                            <th>訂單ID</th>
                            <th>交易對</th>
                            <th>方向</th>
                            <th>類型</th>
                            <th>數量</th>
                            <th>已執行</th>
                            <th>價格</th>
                            <th>手續費</th>
                            <th>狀態</th>
                            <th>時間</th>
                            <th>模式</th>
                        </tr>
                    </thead>
                    <tbody id="history-orders-body">
                        <tr><td colspan="11">載入中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            async function loadOrdersSummary() {
                try {
                    const response = await fetch('/api/orders/summary');
                    const summary = await response.json();
                    
                    document.getElementById('open-orders-count').textContent = summary.open_orders;
                    document.getElementById('today-trades').textContent = summary.todays_trades;
                    document.getElementById('total-volume').textContent = summary.total_volume.toLocaleString();
                    document.getElementById('trading-mode').textContent = summary.trading_mode;
                } catch (error) {
                    console.error('Error loading summary:', error);
                }
            }
            
            async function loadOpenOrders() {
                try {
                    const response = await fetch('/api/orders/open');
                    const orders = await response.json();
                    
                    const tbody = document.getElementById('open-orders-body');
                    if (orders.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9">沒有未完成訂單</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = orders.map(order => `
                        <tr>
                            <td>${order.orderId}</td>
                            <td>${order.symbol}</td>
                            <td class="${order.side.toLowerCase() === 'buy' ? 'side-buy' : 'side-sell'}">${order.side}</td>
                            <td>${order.type}</td>
                            <td>${order.origQty}</td>
                            <td>${order.price}</td>
                            <td>${order.status}</td>
                            <td>${new Date(order.time).toLocaleString()}</td>
                            <td><button onclick="cancelOrder('${order.symbol}', '${order.orderId}')">取消</button></td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Error loading open orders:', error);
                    document.getElementById('open-orders-body').innerHTML = '<tr><td colspan="9">載入失敗</td></tr>';
                }
            }
            
            async function loadOrderHistory() {
                try {
                    const response = await fetch('/api/orders/history?limit=20');
                    const orders = await response.json();
                    
                    const tbody = document.getElementById('history-orders-body');
                    if (orders.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="11">沒有訂單歷史</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = orders.map(order => `
                        <tr>
                            <td>${order.orderId}</td>
                            <td>${order.symbol}</td>
                            <td class="${order.side.toLowerCase() === 'buy' ? 'side-buy' : 'side-sell'}">${order.side}</td>
                            <td>${order.type}</td>
                            <td>${order.quantity}</td>
                            <td>${order.executed_quantity}</td>
                            <td>$${parseFloat(order.price).toFixed(2)}</td>
                            <td>$${parseFloat(order.commission).toFixed(4)}</td>
                            <td class="${order.status.toLowerCase() === 'filled' ? 'status-filled' : 'status-canceled'}">${order.status}</td>
                            <td>${order.time}</td>
                            <td><span class="trading-mode">${order.trading_mode}</span></td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Error loading order history:', error);
                    document.getElementById('history-orders-body').innerHTML = '<tr><td colspan="11">載入失敗</td></tr>';
                }
            }
            
            async function cancelOrder(symbol, orderId) {
                if (!confirm('確定要取消這個訂單嗎？')) return;
                
                try {
                    const response = await fetch('/api/orders/cancel', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol, order_id: orderId })
                    });
                    const data = await response.json();
                    alert(data.message);
                    loadOpenOrders();
                    loadOrderHistory();
                    loadOrdersSummary();
                } catch (error) {
                    alert('取消訂單失敗: ' + error.message);
                }
            }
            
            function loadAllData() {
                loadOrdersSummary();
                loadOpenOrders();
                loadOrderHistory();
            }
            
            // 初始載入
            loadAllData();
            
            // 每30秒更新一次
            setInterval(loadAllData, 30000);
        </script>
    </body>
    </html>
    """

@router.get("/positions", response_class=HTMLResponse)
async def positions_page():
    """Positions page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Positions - Binance Trading Bot</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            .profit { color: #28a745; }
            .loss { color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px;">
                <a href="/" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Dashboard</a>
                <a href="/orders" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Orders</a>
                <a href="/positions" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; background: #007bff;">Positions</a>
                <a href="/history" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">History</a>
            </div>
            
            <h1>📊 Positions</h1>
            
            <div class="card">
                <h2>Active Positions</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Size</th>
                            <th>Entry Price</th>
                            <th>Mark Price</th>
                            <th>PnL</th>
                            <th>ROE%</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="positions-body">
                        <tr><td colspan="7">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            async function loadPositions() {
                try {
                    const response = await fetch('/api/positions/');
                    const positions = await response.json();
                    
                    const tbody = document.getElementById('positions-body');
                    const activePositions = positions.filter(pos => parseFloat(pos.positionAmt) !== 0);
                    
                    if (activePositions.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7">No active positions</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = activePositions.map(pos => `
                        <tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.positionAmt}</td>
                            <td>$${parseFloat(pos.entryPrice).toFixed(4)}</td>
                            <td>$${parseFloat(pos.markPrice).toFixed(4)}</td>
                            <td class="${parseFloat(pos.unRealizedProfit) >= 0 ? 'profit' : 'loss'}">
                                $${parseFloat(pos.unRealizedProfit).toFixed(2)}
                            </td>
                            <td class="${parseFloat(pos.percentage) >= 0 ? 'profit' : 'loss'}">
                                ${parseFloat(pos.percentage).toFixed(2)}%
                            </td>
                            <td>
                                <button onclick="closePosition('${pos.symbol}')">Close</button>
                            </td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Error loading positions:', error);
                }
            }
            
            async function closePosition(symbol) {
                try {
                    const response = await fetch('/api/positions/futures/close', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol })
                    });
                    const data = await response.json();
                    alert(data.message);
                    loadPositions();
                } catch (error) {
                    alert('Error closing position: ' + error.message);
                }
            }
            
            loadPositions();
            setInterval(loadPositions, 30000);
        </script>
    </body>
    </html>
    """

@router.get("/history", response_class=HTMLResponse)
async def history_page():
    """Trading history page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>History - Binance Trading Bot</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            .profit { color: #28a745; }
            .loss { color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="background: #333; padding: 10px; margin-bottom: 20px; border-radius: 8px;">
                <a href="/" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Dashboard</a>
                <a href="/orders" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Orders</a>
                <a href="/positions" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px;">Positions</a>
                <a href="/history" style="color: white; text-decoration: none; margin-right: 20px; padding: 8px 15px; border-radius: 4px; background: #007bff;">History</a>
            </div>
            
            <h1>📈 Trading History</h1>
            
            <div class="card">
                <h2>Recent Trades</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>Quantity</th>
                            <th>PnL</th>
                            <th>%</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody id="history-body">
                        <tr><td colspan="9">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            async function loadHistory() {
                try {
                    const response = await fetch('/api/trading/history');
                    const trades = await response.json();
                    
                    const tbody = document.getElementById('history-body');
                    if (trades.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9">No trading history</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = trades.map(trade => `
                        <tr>
                            <td>${new Date(trade.entry_time).toLocaleString()}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.side}</td>
                            <td>$${trade.entry_price.toFixed(4)}</td>
                            <td>$${trade.exit_price.toFixed(4)}</td>
                            <td>${trade.quantity}</td>
                            <td class="${trade.pnl >= 0 ? 'profit' : 'loss'}">$${trade.pnl.toFixed(2)}</td>
                            <td class="${trade.pnl_percent >= 0 ? 'profit' : 'loss'}">${trade.pnl_percent.toFixed(2)}%</td>
                            <td>${trade.duration}</td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Error loading history:', error);
                }
            }
            
            loadHistory();
            setInterval(loadHistory, 60000);
        </script>
    </body>
    </html>
    """
