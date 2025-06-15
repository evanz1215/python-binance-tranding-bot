"""
Orders-related API routes
"""
from typing import Dict, List
from datetime import datetime
from fastapi import APIRouter, HTTPException

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ...binance_client import binance_client
from ...config import config
from ... import shared_state

def get_client():
    """獲取統一的客戶端實例"""
    if config.binance.paper_trading:
        paper_client = shared_state.get_paper_trading_client()
        if paper_client:
            return paper_client
    # Fallback to binance_client
    return binance_client

router = APIRouter()

@router.get("/open")
async def get_open_orders():
    """Get all open orders"""
    try:
        client = get_client()
        if hasattr(client, 'get_open_orders'):
            orders = client.get_open_orders()
        else:
            orders = []
        return orders if orders else []
    except Exception as e:
        logger.error(f"Error getting open orders: {e}")
        return []


@router.get("/history")
async def get_order_history(limit: int = 50):
    """Get order history"""
    try:
        client = get_client()
        if config.binance.paper_trading and hasattr(client, 'paper_orders'):
            orders = client.paper_orders[-limit:] if client.paper_orders else []
        elif hasattr(client, 'get_order_history'):
            orders = client.get_order_history(limit)
        else:
            orders = []
        # 格式化訂單數據以便前端顯示
        formatted_orders = []
        for order in orders:
            formatted_order = {
                "orderId": order.get("orderId"),
                "symbol": order.get("symbol"),
                "side": order.get("side"),
                "type": order.get("type"),
                "quantity": order.get("origQty"),
                "executed_quantity": order.get("executedQty"),
                "price": order.get("price"),
                "status": order.get("status"),
                "time": datetime.fromtimestamp(order.get("time", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S") if order.get("time") else "N/A",
                "commission": order.get("commission", "0"),
                "trading_mode": "📋 紙上交易" if config.binance.paper_trading else ("🎮 模擬交易" if config.binance.demo_mode else "真實交易")
            }
            formatted_orders.append(formatted_order)
        return formatted_orders
    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        return []


@router.get("/summary")
async def get_orders_summary():
    """Get orders summary statistics"""
    try:
        open_orders = binance_client.get_open_orders()
        
        # 初始化摘要數據
        summary = {
            "open_orders": len(open_orders) if open_orders else 0,
            "todays_trades": 0,
            "total_volume": 0.0,
            "success_rate": 0.0,
            "avg_trade_size": 0.0,
            "trading_mode": "真實交易"
        }
          # 如果是 paper trading 模式，計算虛擬交易統計
        if config.binance.paper_trading:
            orders = binance_client.get_order_history(100)  # 獲取更多訂單用於統計
            
            total_orders = len(orders)
            filled_orders = [o for o in orders if o.get("status") == "FILLED"]
            
            # 計算總交易量
            total_volume = sum(
                float(order.get("executedQty", 0)) * float(order.get("price", 0))
                for order in filled_orders
            )
            
            # 計算平均交易大小
            avg_trade_size = total_volume / len(filled_orders) if filled_orders else 0
            
            summary.update({
                "todays_trades": len(filled_orders),
                "total_volume": round(total_volume, 2),
                "success_rate": 100.0 if filled_orders else 0.0,  # Paper trading 所有訂單都成功
                "avg_trade_size": round(avg_trade_size, 2),
                "trading_mode": "📋 紙上交易"
            })
            
        elif config.binance.demo_mode:
            summary.update({
                "todays_trades": 5,
                "total_volume": 12500.0,
                "success_rate": 100.0,
                "avg_trade_size": 2500.0,
                "trading_mode": "🎮 模擬交易"
            })
        
        return summary
    except Exception as e:
        logger.error(f"Error getting orders summary: {e}")
        return {
            "open_orders": 0,
            "todays_trades": 0,
            "total_volume": 0.0,
            "success_rate": 0.0,
            "avg_trade_size": 0.0,
            "trading_mode": "錯誤"
        }


@router.post("/cancel")
async def cancel_order(request: Dict[str, str]):
    """Cancel an order"""
    try:
        symbol = request.get("symbol")
        order_id = request.get("order_id")
        
        if not symbol or not order_id:
            raise HTTPException(status_code=400, detail="Symbol and order_id are required")        # 根據交易模式處理取消訂單
        if config.binance.paper_trading:
            result = binance_client.cancel_futures_order(
                symbol=symbol,
                order_id=order_id
            )
            return {"message": "虛擬訂單已取消", "result": result, "trading_mode": "📋 紙上交易"}
        elif config.binance.demo_mode:
            # Demo 模式也返回成功
            return {
                "message": "模擬訂單已取消", 
                "result": {"orderId": order_id, "symbol": symbol, "status": "CANCELED"},
                "trading_mode": "🎮 模擬交易"
            }
        else:
            # 真實交易模式
            result = binance_client.cancel_order(symbol, order_id)
            return {"message": "訂單已取消", "result": result, "trading_mode": "真實交易"}
        
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
