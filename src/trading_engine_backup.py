"""
Main trading engine that orchestrates all components
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from .config import config
from .binance_client import binance_client
from .data_manager_fixed import data_manager
from .risk_manager import risk_manager
from .strategies import get_strategy, Signal
from .database.models import (
    Strategy as StrategyModel, Position, Trade, 
    TradingSession, get_session_factory
)


class TradingEngine:
    """Main trading engine"""
    
    def __init__(self, strategy_name: str = "ma_cross", **strategy_params):
        self.strategy = get_strategy(strategy_name, **strategy_params)
        self.session_factory = get_session_factory(config.database.url)
        self.is_running = False
        self.session_id = None
        self.monitored_symbols = []
        self.last_analysis_time = {}
          def get_session(self) -> Session:
        """Get database session"""
        return self.session_factory()
    
    async def start(self) -> None:
        """Start the trading engine"""
        try:
            logger.info("Starting trading engine...")
            
            # Set running status first
            self.is_running = True
            
            # Initialize components
            await self._initialize()
            
            # Start main trading loop in background
            logger.info("Trading engine initialization completed, starting main loop...")
            asyncio.create_task(self._main_loop())
            
        except Exception as e:
            logger.error(f"Trading engine initialization error: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the trading engine"""
        try:
            logger.info("Stopping trading engine...")
            self.is_running = False
            
            # Close any remaining positions if configured to do so
            await self._emergency_stop()
            
            # Update session
            if self.session_id:
                with self.get_session() as session:
                    trading_session = session.query(TradingSession).filter_by(
                        session_id=self.session_id
                    ).first()
                    
                    if trading_session:
                        trading_session.end_time = datetime.utcnow()
                        trading_session.status = "STOPPED"
                        session.commit()
            
            logger.info("Trading engine stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
    
    async def _initialize(self) -> None:
        """Initialize trading engine components"""
        try:
            # Initialize risk manager
            risk_manager.initialize_session()
            
            # Update symbol information
            data_manager.update_symbol_info()
            
            # Get symbols to monitor
            self.monitored_symbols = self._get_monitored_symbols()
            logger.info(f"Monitoring {len(self.monitored_symbols)} symbols")
            
            # Create trading session
            self.session_id = f"session_{int(datetime.utcnow().timestamp())}"
            
            balance = binance_client.get_balance(config.trading.base_currency)
            initial_balance = balance.get('total', 0.0)
            
            with self.get_session() as session:
                trading_session = TradingSession(
                    session_id=self.session_id,
                    start_time=datetime.utcnow(),
                    initial_balance=initial_balance,
                    current_balance=initial_balance,
                    status="ACTIVE"
                )
                session.add(trading_session)
                session.commit()
            
            # Ensure we have enough market data
            await self._ensure_market_data()
            
            logger.info("Trading engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading engine: {e}")
            raise
    
    async def _main_loop(self) -> None:
        """Main trading loop"""
        loop_interval = 60  # seconds between analysis cycles
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Update market data
                await self._update_market_data()
                
                # Analyze all symbols
                signals = await self._analyze_all_symbols()
                
                # Process trading signals
                await self._process_signals(signals)
                
                # Update positions
                await self._update_positions()
                
                # Update session statistics
                await self._update_session_stats()
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, loop_interval - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in main trading loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    def _get_monitored_symbols(self) -> List[str]:
        """Get list of symbols to monitor"""
        try:
            # Get active symbols from Binance
            active_symbols = binance_client.filter_symbols_by_criteria(
                min_volume_24h=config.trading.min_volume_24h,
                max_symbols=50  # Limit to top 50 by volume
            )
            
            # Apply whitelist/blacklist filters
            filtered_symbols = []
            for symbol in active_symbols:
                # Apply whitelist
                if config.trading.whitelist and symbol not in config.trading.whitelist:
                    continue
                
                # Apply blacklist
                if config.trading.blacklist and symbol in config.trading.blacklist:
                    continue
                
                filtered_symbols.append(symbol)
            
            return filtered_symbols[:config.trading.max_positions * 2]  # Monitor 2x max positions
            
        except Exception as e:
            logger.error(f"Error getting monitored symbols: {e}")
            return []
    
    async def _ensure_market_data(self) -> None:
        """Ensure we have enough market data for analysis"""
        try:
            required_timeframes = self.strategy.get_required_timeframes()
            required_periods = self.strategy.get_required_periods()
            
            logger.info("Ensuring market data availability...")
            
            for symbol in self.monitored_symbols:
                for timeframe in required_timeframes:
                    success = data_manager.ensure_data_availability(
                        symbol, timeframe, required_periods
                    )
                    if not success:
                        logger.warning(f"Could not ensure data for {symbol} {timeframe}")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)
            
            logger.info("Market data check completed")
            
        except Exception as e:
            logger.error(f"Error ensuring market data: {e}")
    
    async def _update_market_data(self) -> None:
        """Update market data for monitored symbols"""
        try:
            required_timeframes = self.strategy.get_required_timeframes()
            
            # Update data for all symbols (with rate limiting)
            await data_manager.update_all_market_data(
                self.monitored_symbols, required_timeframes
            )
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def _analyze_all_symbols(self) -> List[Signal]:
        """Analyze all monitored symbols for trading signals"""
        signals = []
        
        try:
            required_timeframes = self.strategy.get_required_timeframes()
            required_periods = self.strategy.get_required_periods()
            
            for symbol in self.monitored_symbols:
                try:
                    # Get market data for primary timeframe
                    primary_timeframe = required_timeframes[0]
                    df = data_manager.get_market_data(
                        symbol, primary_timeframe, limit=required_periods
                    )
                    
                    if df.empty or len(df) < required_periods:
                        logger.debug(f"Insufficient data for {symbol}")
                        continue
                    
                    # Analyze with strategy
                    signal = self.strategy.analyze(symbol, df)
                    
                    if signal.action != "HOLD":
                        signals.append(signal)
                        logger.info(f"Signal: {signal}")
                    
                    # Update last analysis time
                    self.last_analysis_time[symbol] = datetime.utcnow()
                    
                except Exception as e:
                    logger.warning(f"Error analyzing {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in symbol analysis: {e}")
            return []
    
    async def _process_signals(self, signals: List[Signal]) -> None:
        """Process trading signals and execute trades"""
        try:
            for signal in signals:
                try:
                    await self._process_single_signal(signal)
                except Exception as e:
                    logger.error(f"Error processing signal {signal}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error processing signals: {e}")
    
    async def _process_single_signal(self, signal: Signal) -> None:
        """Process a single trading signal"""
        try:
            symbol = signal.symbol
            action = signal.action
            
            # Get current price
            ticker = binance_client.get_24hr_ticker(symbol)
            current_price = float(ticker['lastPrice'])
            
            # Check if we have existing position
            existing_position = symbol in risk_manager.positions
            
            if action == "BUY" and not existing_position:
                await self._execute_buy_order(signal, current_price)
            elif action == "SELL" and existing_position:
                await self._execute_sell_order(signal, current_price)
            elif action == "SELL" and not existing_position:
                # Could implement short selling here if enabled
                logger.debug(f"Ignoring SELL signal for {symbol} - no position")
            elif action == "BUY" and existing_position:
                # Could implement position sizing/averaging here
                logger.debug(f"Ignoring BUY signal for {symbol} - already have position")
            
        except Exception as e:
            logger.error(f"Error processing signal for {signal.symbol}: {e}")
    
    async def _execute_buy_order(self, signal: Signal, current_price: float) -> None:
        """Execute a buy order"""
        try:
            symbol = signal.symbol
            
            # Get available balance
            balance = binance_client.get_balance(config.trading.base_currency)
            available_balance = balance.get('free', 0.0)
            
            # Calculate position size
            position_size = self.strategy.calculate_position_size(
                symbol, signal, available_balance, current_price
            )
            
            # Check risk management
            can_trade, reason = risk_manager.can_open_position(
                symbol, "BUY", position_size
            )
            
            if not can_trade:
                logger.warning(f"Cannot open BUY position for {symbol}: {reason}")
                return
            
            # Calculate quantity
            quantity = binance_client.calculate_quantity(symbol, position_size, current_price)
            
            # Place market order
            order = binance_client.place_order(
                symbol=symbol,
                side="BUY",
                order_type="MARKET",
                quantity=quantity
            )
            
            if order['status'] == 'FILLED':
                # Calculate actual fill price and quantity
                fill_price = float(order['fills'][0]['price']) if order['fills'] else current_price
                fill_quantity = float(order['executedQty'])
                
                # Add to risk manager
                risk_manager.add_position(
                    symbol=symbol,
                    side="BUY",
                    quantity=fill_quantity,
                    entry_price=fill_price
                )
                
                # Record trade in database
                await self._record_trade(order, signal, "BUY")
                
                logger.info(f"BUY order executed: {symbol} {fill_quantity} @ {fill_price}")
            
        except Exception as e:
            logger.error(f"Error executing BUY order for {signal.symbol}: {e}")
    
    async def _execute_sell_order(self, signal: Signal, current_price: float) -> None:
        """Execute a sell order"""
        try:
            symbol = signal.symbol
            
            # Get position info
            if symbol not in risk_manager.positions:
                logger.warning(f"No position found for {symbol}")
                return
            
            position = risk_manager.positions[symbol]
            quantity = position['quantity']
            
            # Check risk management
            can_trade, reason = risk_manager.can_close_position(symbol)
            
            if not can_trade:
                logger.warning(f"Cannot close position for {symbol}: {reason}")
                return
            
            # Place market order to close position
            order = binance_client.place_order(
                symbol=symbol,
                side="SELL",
                order_type="MARKET",
                quantity=quantity
            )
            
            if order['status'] == 'FILLED':
                # Remove from risk manager
                risk_manager.remove_position(symbol)
                
                # Record trade in database
                await self._record_trade(order, signal, "SELL")
                
                fill_price = float(order['fills'][0]['price']) if order['fills'] else current_price
                logger.info(f"SELL order executed: {symbol} {quantity} @ {fill_price}")
            
        except Exception as e:
            logger.error(f"Error executing SELL order for {signal.symbol}: {e}")
    
    async def _record_trade(self, order: Dict[str, Any], signal: Signal, side: str) -> None:
        """Record trade in database"""
        try:
            with self.get_session() as session:
                # Get or create strategy record
                strategy_record = session.query(StrategyModel).filter_by(
                    name=self.strategy.name
                ).first()
                
                if not strategy_record:
                    strategy_record = StrategyModel(
                        name=self.strategy.name,
                        description=f"Strategy: {self.strategy.name}",
                        parameters=self.strategy.parameters
                    )
                    session.add(strategy_record)
                    session.flush()
                
                # Create trade record
                trade = Trade(
                    symbol=signal.symbol,
                    strategy_id=strategy_record.id,
                    order_id=order['orderId'],
                    side=side,
                    type=order['type'],
                    quantity=float(order['executedQty']),
                    price=float(order['fills'][0]['price']) if order['fills'] else 0.0,
                    fee=sum(float(fill['commission']) for fill in order['fills']),
                    status=order['status'],
                    timestamp=datetime.utcnow()
                )
                
                session.add(trade)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    async def _update_positions(self) -> None:
        """Update all positions with current prices and check stop/take profit"""
        try:
            for symbol in list(risk_manager.positions.keys()):
                try:
                    # Get current price
                    ticker = binance_client.get_24hr_ticker(symbol)
                    current_price = float(ticker['lastPrice'])
                    
                    # Update position and check triggers
                    triggers = risk_manager.update_position_prices(symbol, current_price)
                    
                    # Handle stop loss
                    if triggers['stop_loss_triggered']:
                        logger.warning(f"Stop loss triggered for {symbol}")
                        signal = Signal(symbol, "SELL", 1.0, "Stop loss triggered")
                        await self._execute_sell_order(signal, current_price)
                    
                    # Handle take profit
                    elif triggers['take_profit_triggered']:
                        logger.info(f"Take profit triggered for {symbol}")
                        signal = Signal(symbol, "SELL", 1.0, "Take profit triggered")
                        await self._execute_sell_order(signal, current_price)
                    
                except Exception as e:
                    logger.warning(f"Error updating position for {symbol}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    async def _update_session_stats(self) -> None:
        """Update trading session statistics"""
        try:
            if not self.session_id:
                return
            
            balance = binance_client.get_balance(config.trading.base_currency)
            current_balance = balance.get('total', 0.0)
            
            with self.get_session() as session:
                trading_session = session.query(TradingSession).filter_by(
                    session_id=self.session_id
                ).first()
                
                if trading_session:
                    trading_session.current_balance = current_balance
                    trading_session.total_pnl = current_balance - trading_session.initial_balance
                    
                    # Count trades in this session
                    trades_count = session.query(Trade).filter(
                        Trade.timestamp >= trading_session.start_time
                    ).count()
                    
                    trading_session.trades_count = trades_count
                    session.commit()
            
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")
    
    async def _emergency_stop(self) -> None:
        """Emergency stop - close all positions"""
        try:
            logger.warning("Emergency stop initiated - closing all positions")
            
            for symbol in list(risk_manager.positions.keys()):
                try:
                    # Get current price
                    ticker = binance_client.get_24hr_ticker(symbol)
                    current_price = float(ticker['lastPrice'])
                    
                    # Create emergency sell signal
                    signal = Signal(symbol, "SELL", 1.0, "Emergency stop")
                    await self._execute_sell_order(signal, current_price)
                    
                except Exception as e:
                    logger.error(f"Error closing position {symbol} during emergency stop: {e}")
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading engine status"""
        try:
            risk_metrics = risk_manager.get_current_metrics()
            
            return {
                'is_running': self.is_running,
                'session_id': self.session_id,
                'strategy': self.strategy.name,
                'monitored_symbols': len(self.monitored_symbols),
                'active_positions': len(risk_manager.positions),
                'risk_level': risk_metrics.risk_level,
                'total_balance': risk_metrics.total_balance,
                'daily_pnl': risk_metrics.daily_pnl,
                'last_update': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}
