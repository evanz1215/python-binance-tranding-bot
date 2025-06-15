"""
Positions-related API routes
"""
from typing import Dict
from fastapi import APIRouter, HTTPException

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ...binance_client import binance_client

router = APIRouter()

@router.get("/")
async def get_positions():
    """Get current positions"""
    try:
        from ...binance_client import binance_client, get_client
        from ...config import config
        
        # 檢查是否有有效的憑證
        if not config.binance.has_valid_credentials("futures"):
            raise HTTPException(
                status_code=400, 
                detail="No valid futures API credentials configured. Please check your .env file."
            )
        
        # 使用合約客戶端
        client = get_client("futures") or binance_client
        if client is None:
            raise HTTPException(
                status_code=500,
                detail="Binance client not initialized"
            )
            
        positions = client.get_futures_positions()
        return positions
        
    except Exception as e:
        error_msg = str(e)
        
        # 提供更友好的錯誤訊息
        if "APIError(code=-2015)" in error_msg:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "API權限錯誤",
                    "message": "API金鑰無效、IP不在白名單中，或沒有期貨交易權限",
                    "suggestions": [
                        "檢查您的 BINANCE_FUTURES_API_KEY 和 BINANCE_FUTURES_SECRET_KEY 是否正確",
                        "確認API金鑰已啟用期貨交易權限",
                        "檢查IP是否在Binance API白名單中",
                        "如果使用testnet，請確認使用的是testnet的API金鑰"
                    ]
                }
            )
        elif "APIError(code=-1021)" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="時間戳錯誤，請檢查系統時間是否同步"
            )
        else:
            logger.error(f"Error getting positions: {e}")
            raise HTTPException(status_code=500, detail=f"獲取持倉失敗: {error_msg}")


@router.post("/futures/close")
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
