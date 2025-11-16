"""
Grid Trading Strategy Implementation for CoinDCX
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from coindcx_client import CoinDCXFuturesClient
from logger import TradingLogger


class GridTraderCoinDCX:
    """Implements the grid trading strategy for SOL/USDT on CoinDCX"""

    def __init__(self, client: CoinDCXFuturesClient, config: Dict[str, Any], logger: TradingLogger):
        """
        Initialize Grid Trader

        Args:
            client: CoinDCXFuturesClient instance
            config: Trading configuration
            logger: TradingLogger instance
        """
        self.client = client
        self.config = config
        self.logger = logger

        # Trading parameters
        self.market = config['trading']['market']  # e.g., 'SOLUSDT'
        self.buy_level = config['trading']['buy_level']
        self.sell_level = config['trading']['sell_level']
        self.position_size = config['trading']['position_size']
        self.leverage = config['trading']['leverage']
        self.order_type = config['trading']['order_type']
        self.trade_direction = config['trading'].get('trade_direction', 'long')  # 'long', 'short', or 'both'

        # Safety parameters
        self.max_loss = config['safety']['max_cumulative_loss']
        self.stop_loss_percentage = config['safety'].get('stop_loss_percentage', 5)  # Default 5%
        self.support_level = config['safety']['support_level']
        self.resistance_level = config['safety']['resistance_level']
        self.trading_range_min = config['safety']['trading_range_min']
        self.trading_range_max = config['safety']['trading_range_max']

        # State tracking - support both long and short positions simultaneously
        self.long_position = None
        self.long_entry_price = None
        self.short_position = None
        self.short_entry_price = None
        self.trades = []
        self.cumulative_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.is_running = False  # Start as False, set to True when run() is called
        self.bot_state = "stopped"  # Start as stopped
        self.error_message = None

        # Reporting
        self.last_hourly_report = datetime.now()
        self.last_daily_report = datetime.now()
        self.hourly_trades_start = 0
        self.daily_trades_start = 0

    def initialize(self) -> bool:
        """
        Initialize the trading bot

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("SOL/USDT GRID TRADING BOT - COINDCX - INITIALIZING")
        self.logger.info("=" * 60)

        # Test connection
        if not self.client.test_connection():
            error_msg = "API Connection Failed - Check credentials in .env file"
            self.logger.error(f"Failed to connect to CoinDCX API - {error_msg}")
            self.logger.error("Common issues:")
            self.logger.error("  1. Wrong API key or secret")
            self.logger.error("  2. API key doesn't have futures trading permissions")
            self.logger.error("  3. IP whitelist restriction on CoinDCX")
            self.logger.error("  4. API endpoint /exchange/v1/users/info returning 401/403")
            self.bot_state = "error"
            self.error_message = error_msg
            return False

        # Display configuration
        # Note: Leverage is set per-order in CoinDCX, not per-position
        self.logger.info(f"Trading Market: {self.market}")
        self.logger.info(f"Trade Direction: {self.trade_direction.upper()}")
        self.logger.info(f"Buy Level: ${self.buy_level:.2f}")
        self.logger.info(f"Sell Level: ${self.sell_level:.2f}")
        self.logger.info(f"Grid Range: ${self.sell_level - self.buy_level:.2f}")
        self.logger.info(f"Position Size: {self.position_size} SOL (Dynamic sizing enabled)")
        self.logger.info(f"Leverage: {self.leverage}x")
        self.logger.info(f"Order Type: {self.order_type}")
        self.logger.info(f"Stop-Loss: {self.stop_loss_percentage}% per trade")
        self.logger.info(f"Max Cumulative Loss: ${self.max_loss:.2f}")
        self.logger.info(f"Trading Range: ${self.trading_range_min:.2f} - ${self.trading_range_max:.2f}")
        self.logger.info("=" * 60)

        # Check for existing positions
        position = self.client.get_position(self.market)
        if position:
            side = position.get('side', '').lower()
            if side == 'long':
                self.logger.warning(f"Existing LONG position detected: {position['size']} @ ${position['entry_price']:.2f}")
                self.long_position = position
                self.long_entry_price = position['entry_price']
            elif side == 'short':
                self.logger.warning(f"Existing SHORT position detected: {position['size']} @ ${position['entry_price']:.2f}")
                self.short_position = position
                self.short_entry_price = position['entry_price']

        # Don't set bot_state to "running" here - let run() method do it
        # bot_state will be "stopped" until run() is called
        return True

    def check_price_and_trade(self) -> bool:
        """
        Check current price and execute trades if conditions are met
        Supports long, short, or both trading directions

        Returns:
            True if trading should continue, False to stop
        """
        # Get current price
        current_price = self.client.get_current_price(self.market)
        if current_price is None:
            self.logger.error("Failed to fetch current price")
            return False

        # Check if price is within trading range
        if current_price < self.trading_range_min or current_price > self.trading_range_max:
            if not hasattr(self, '_range_warning_shown') or not self._range_warning_shown:
                self.logger.warning(f"Price ${current_price:.2f} is outside trading range ${self.trading_range_min:.2f}-${self.trading_range_max:.2f}. PAUSING TRADING.")
                self._range_warning_shown = True
                self.bot_state = "paused"
            return True
        else:
            self._range_warning_shown = False
            if self.bot_state == "paused":
                self.bot_state = "running"

        # Check for support/resistance breach
        if current_price <= self.support_level:
            self.logger.alert(f"Price ${current_price:.2f} breached support level ${self.support_level:.2f}")
        elif current_price >= self.resistance_level:
            self.logger.alert(f"Price ${current_price:.2f} breached resistance level ${self.resistance_level:.2f}")

        # Get current positions from exchange
        position = self.client.get_position(self.market)

        # Sync internal position tracking with exchange positions
        # This ensures the bot tracks manually placed orders correctly
        if position:
            if position.get('side') == 'buy':
                # Update long position tracking
                self.long_position = position
                if position.get('entry_price'):
                    self.long_entry_price = position['entry_price']
                # Clear short position if exchange shows long
                self.short_position = None
                self.short_entry_price = None
            elif position.get('side') == 'sell':
                # Update short position tracking
                self.short_position = position
                if position.get('entry_price'):
                    self.short_entry_price = position['entry_price']
                # Clear long position if exchange shows short
                self.long_position = None
                self.long_entry_price = None
        else:
            # No position on exchange - clear both internal positions
            self.long_position = None
            self.long_entry_price = None
            self.short_position = None
            self.short_entry_price = None

        has_long = self.long_position is not None and self.long_position.get('size', 0) > 0
        has_short = self.short_position is not None and self.short_position.get('size', 0) > 0

        # Check for per-trade stop-loss on LONG position
        if has_long and self.long_entry_price:
            loss_percentage = ((current_price - self.long_entry_price) / self.long_entry_price) * 100

            if loss_percentage <= -self.stop_loss_percentage:
                self.logger.alert(f"LONG stop-loss triggered! Current loss: {loss_percentage:.2f}% (Entry: ${self.long_entry_price:.2f}, Current: ${current_price:.2f})")

                # Close long position immediately
                if self._execute_stop_loss(current_price, loss_percentage, 'long'):
                    self.logger.warning(f"LONG position closed at ${current_price:.2f} due to {self.stop_loss_percentage}% stop-loss")

        # Check for per-trade stop-loss on SHORT position
        if has_short and self.short_entry_price:
            # For short positions, profit when price goes down, loss when price goes up
            loss_percentage = ((self.short_entry_price - current_price) / self.short_entry_price) * 100

            if loss_percentage <= -self.stop_loss_percentage:
                self.logger.alert(f"SHORT stop-loss triggered! Current loss: {loss_percentage:.2f}% (Entry: ${self.short_entry_price:.2f}, Current: ${current_price:.2f})")

                # Close short position immediately
                if self._execute_stop_loss(current_price, loss_percentage, 'short'):
                    self.logger.warning(f"SHORT position closed at ${current_price:.2f} due to {self.stop_loss_percentage}% stop-loss")

        # Execute LONG trading logic
        if self.trade_direction in ['long', 'both']:
            # BUY at buy_level if no long position
            if current_price <= self.buy_level and not has_long:
                if self._execute_long_entry(current_price):
                    self.total_trades += 1

            # SELL (close long) at sell_level if long position exists
            elif current_price >= self.sell_level and has_long:
                if self._execute_long_exit(current_price):
                    self.total_trades += 1

        # Execute SHORT trading logic
        if self.trade_direction in ['short', 'both']:
            # SHORT SELL at sell_level if no short position
            if current_price >= self.sell_level and not has_short:
                if self._execute_short_entry(current_price):
                    self.total_trades += 1

            # BUY BACK (close short) at buy_level if short position exists
            elif current_price <= self.buy_level and has_short:
                if self._execute_short_exit(current_price):
                    self.total_trades += 1

        # Check if cumulative loss exceeds limit
        if self.cumulative_pnl <= self.max_loss:
            self.logger.alert(f"Cumulative loss ${self.cumulative_pnl:.2f} exceeds limit ${self.max_loss:.2f}. STOPPING TRADING.")
            self.bot_state = "stopped"
            return False

        return True

    def _execute_long_entry(self, current_price: float) -> bool:
        """
        Execute LONG entry (BUY) using all available USDT balance with leverage

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            # Get available USDT balance from wallet
            wallet_details = self.client.get_wallet_details()
            if not wallet_details:
                self.logger.error("Failed to get wallet details")
                return False

            # Find USDT balance
            usdt_balance = 0
            for wallet in wallet_details:
                currency = wallet.get('currency_short_name') or wallet.get('margin_currency_short_name') or wallet.get('currency')
                if currency == 'USDT':
                    usdt_balance = float(wallet.get('balance', 0))
                    break

            if usdt_balance <= 0:
                self.logger.warning("No USDT balance available for LONG entry")
                return False

            # Calculate position size: (USDT balance * leverage) / price
            # Reserve small amount for fees (use 99% of balance)
            usable_balance = usdt_balance * 0.99
            position_size = (usable_balance * self.leverage) / current_price

            # Round to appropriate precision (CoinDCX SOL precision - 2 decimals)
            position_size = round(position_size, 2)

            self.logger.info(f"LONG entry sizing: {position_size} SOL (Balance: ${usdt_balance:.2f}, Leverage: {self.leverage}x, Price: ${current_price:.2f})")

            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'buy', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'buy', position_size, self.buy_level, self.leverage)
                execution_price = self.buy_level

            if order:
                self.long_entry_price = execution_price
                self.long_position = {'side': 'long', 'size': position_size, 'entry_price': execution_price}
                self.logger.trade_execution('LONG ENTRY (BUY)', position_size, execution_price)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'LONG_ENTRY',
                    'price': execution_price,
                    'quantity': position_size,
                    'order_id': order.get('id', 'unknown')
                })
                return True

        except Exception as e:
            self.logger.error(f"Error executing LONG entry: {str(e)}")

        return False

    def _execute_long_exit(self, current_price: float) -> bool:
        """
        Execute LONG exit (SELL) to close long position

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            if not self.long_position:
                self.logger.warning("No LONG position to close")
                return False

            # Get actual position size
            position_size = self.long_position['size']

            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'sell', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'sell', position_size, self.sell_level, self.leverage)
                execution_price = self.sell_level

            if order and self.long_entry_price:
                # Calculate profit
                profit = (execution_price - self.long_entry_price) * position_size
                self.cumulative_pnl += profit

                # Update statistics
                if profit > 0:
                    self.winning_trades += 1

                self.logger.trade_execution('LONG EXIT (SELL)', position_size, execution_price, profit)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'LONG_EXIT',
                    'price': execution_price,
                    'quantity': position_size,
                    'profit': profit,
                    'order_id': order.get('id', 'unknown')
                })

                # Reset LONG position
                self.long_position = None
                self.long_entry_price = None

                # Log status
                win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                self.logger.status_update(self.total_trades, win_rate, self.cumulative_pnl)

                return True

        except Exception as e:
            self.logger.error(f"Error executing LONG exit: {str(e)}")

        return False

    def _execute_short_entry(self, current_price: float) -> bool:
        """
        Execute SHORT entry (SELL) using all available USDT balance with leverage

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            # Get available USDT balance from wallet
            wallet_details = self.client.get_wallet_details()
            if not wallet_details:
                self.logger.error("Failed to get wallet details")
                return False

            # Find USDT balance
            usdt_balance = 0
            for wallet in wallet_details:
                currency = wallet.get('currency_short_name') or wallet.get('margin_currency_short_name') or wallet.get('currency')
                if currency == 'USDT':
                    usdt_balance = float(wallet.get('balance', 0))
                    break

            if usdt_balance <= 0:
                self.logger.warning("No USDT balance available for SHORT entry")
                return False

            # Calculate position size: (USDT balance * leverage) / price
            # Reserve small amount for fees (use 99% of balance)
            usable_balance = usdt_balance * 0.99
            position_size = (usable_balance * self.leverage) / current_price

            # Round to appropriate precision (CoinDCX SOL precision - 2 decimals)
            position_size = round(position_size, 2)

            self.logger.info(f"SHORT entry sizing: {position_size} SOL (Balance: ${usdt_balance:.2f}, Leverage: {self.leverage}x, Price: ${current_price:.2f})")

            # Place SHORT order (sell to open)
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'sell', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'sell', position_size, self.sell_level, self.leverage)
                execution_price = self.sell_level

            if order:
                self.short_entry_price = execution_price
                self.short_position = {'side': 'short', 'size': position_size, 'entry_price': execution_price}
                self.logger.trade_execution('SHORT ENTRY (SELL)', position_size, execution_price)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'SHORT_ENTRY',
                    'price': execution_price,
                    'quantity': position_size,
                    'order_id': order.get('id', 'unknown')
                })
                return True

        except Exception as e:
            self.logger.error(f"Error executing SHORT entry: {str(e)}")

        return False

    def _execute_short_exit(self, current_price: float) -> bool:
        """
        Execute SHORT exit (BUY) to close short position

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            if not self.short_position:
                self.logger.warning("No SHORT position to close")
                return False

            # Get actual position size
            position_size = self.short_position['size']

            # Place BUY order to close SHORT
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'buy', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'buy', position_size, self.buy_level, self.leverage)
                execution_price = self.buy_level

            if order and self.short_entry_price:
                # Calculate profit (for short: profit when price goes down)
                profit = (self.short_entry_price - execution_price) * position_size
                self.cumulative_pnl += profit

                # Update statistics
                if profit > 0:
                    self.winning_trades += 1

                self.logger.trade_execution('SHORT EXIT (BUY)', position_size, execution_price, profit)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'SHORT_EXIT',
                    'price': execution_price,
                    'quantity': position_size,
                    'profit': profit,
                    'order_id': order.get('id', 'unknown')
                })

                # Reset SHORT position
                self.short_position = None
                self.short_entry_price = None

                # Log status
                win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                self.logger.status_update(self.total_trades, win_rate, self.cumulative_pnl)

                return True

        except Exception as e:
            self.logger.error(f"Error executing SHORT exit: {str(e)}")

        return False

    def _execute_buy(self, current_price: float) -> bool:
        """
        Execute buy order using all available USDT balance with leverage

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            # Get available USDT balance from wallet
            wallet_details = self.client.get_wallet_details()
            if not wallet_details:
                self.logger.error("Failed to get wallet details")
                return False

            # Find USDT balance
            usdt_balance = 0
            for wallet in wallet_details:
                currency = wallet.get('currency_short_name') or wallet.get('margin_currency_short_name') or wallet.get('currency')
                if currency == 'USDT':
                    usdt_balance = float(wallet.get('balance', 0))
                    break

            if usdt_balance <= 0:
                self.logger.warning("No USDT balance available")
                return False

            # Calculate position size: (USDT balance * leverage) / price
            # Reserve small amount for fees (use 99% of balance)
            usable_balance = usdt_balance * 0.99
            position_size = (usable_balance * self.leverage) / current_price

            # Round to appropriate precision (CoinDCX SOL precision - 2 decimals)
            position_size = round(position_size, 2)

            self.logger.info(f"Dynamic position sizing: {position_size} SOL (Balance: ${usdt_balance:.2f}, Leverage: {self.leverage}x, Price: ${current_price:.2f})")

            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'buy', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'buy', position_size, self.buy_level, self.leverage)
                execution_price = self.buy_level

            if order:
                self.entry_price = execution_price
                self.current_position = {'side': 'long', 'size': position_size, 'entry_price': execution_price}
                self.logger.trade_execution('BUY', position_size, execution_price)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'BUY',
                    'price': execution_price,
                    'quantity': position_size,
                    'order_id': order.get('id', 'unknown')
                })
                return True

        except Exception as e:
            self.logger.error(f"Error executing buy order: {str(e)}")

        return False

    def _execute_sell(self, current_price: float) -> bool:
        """
        Execute sell order

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            # Get actual position size from current position (dynamically calculated during buy)
            position_size = self.current_position['size'] if self.current_position else self.position_size

            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'sell', position_size, current_price, self.leverage)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'sell', position_size, self.sell_level, self.leverage)
                execution_price = self.sell_level

            if order and self.entry_price:
                # Calculate profit
                profit = (execution_price - self.entry_price) * position_size
                self.cumulative_pnl += profit

                # Update statistics
                if profit > 0:
                    self.winning_trades += 1

                self.logger.trade_execution('SELL', position_size, execution_price, profit)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'SELL',
                    'price': execution_price,
                    'quantity': position_size,
                    'profit': profit,
                    'order_id': order.get('id', 'unknown')
                })

                # Reset position
                self.current_position = None
                self.entry_price = None

                # Log status
                win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                self.logger.status_update(self.total_trades, win_rate, self.cumulative_pnl)

                return True

        except Exception as e:
            self.logger.error(f"Error executing sell order: {str(e)}")

        return False

    def _execute_stop_loss(self, current_price: float, loss_percentage: float, position_type: str) -> bool:
        """
        Execute stop-loss by closing position at market price

        Args:
            current_price: Current market price
            loss_percentage: Current loss percentage
            position_type: 'long' or 'short'

        Returns:
            True if stop-loss executed successfully
        """
        try:
            if position_type == 'long':
                if not self.long_position:
                    self.logger.warning("No LONG position to stop-loss")
                    return False

                position_size = self.long_position['size']
                entry_price = self.long_entry_price

                # Close LONG position with SELL order
                order = self.client.place_market_order(self.market, 'sell', position_size, current_price, self.leverage)

                if order and entry_price:
                    # Calculate loss
                    loss = (current_price - entry_price) * position_size
                    self.cumulative_pnl += loss
                    self.total_trades += 1

                    self.logger.trade_execution('LONG STOP-LOSS (SELL)', position_size, current_price, loss)

                    # Record trade
                    self.trades.append({
                        'timestamp': datetime.now(),
                        'type': 'LONG_STOP_LOSS',
                        'price': current_price,
                        'quantity': position_size,
                        'profit': loss,
                        'loss_percentage': loss_percentage,
                        'order_id': order.get('id', 'unknown')
                    })

                    # Reset LONG position
                    self.long_position = None
                    self.long_entry_price = None

                    # Log status
                    win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                    self.logger.status_update(self.total_trades, win_rate, self.cumulative_pnl)

                    return True

            elif position_type == 'short':
                if not self.short_position:
                    self.logger.warning("No SHORT position to stop-loss")
                    return False

                position_size = self.short_position['size']
                entry_price = self.short_entry_price

                # Close SHORT position with BUY order
                order = self.client.place_market_order(self.market, 'buy', position_size, current_price, self.leverage)

                if order and entry_price:
                    # Calculate loss (for short: loss when price goes up)
                    loss = (entry_price - current_price) * position_size
                    self.cumulative_pnl += loss
                    self.total_trades += 1

                    self.logger.trade_execution('SHORT STOP-LOSS (BUY)', position_size, current_price, loss)

                    # Record trade
                    self.trades.append({
                        'timestamp': datetime.now(),
                        'type': 'SHORT_STOP_LOSS',
                        'price': current_price,
                        'quantity': position_size,
                        'profit': loss,
                        'loss_percentage': loss_percentage,
                        'order_id': order.get('id', 'unknown')
                    })

                    # Reset SHORT position
                    self.short_position = None
                    self.short_entry_price = None

                    # Log status
                    win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                    self.logger.status_update(self.total_trades, win_rate, self.cumulative_pnl)

                    return True

        except Exception as e:
            self.logger.error(f"Error executing stop-loss for {position_type}: {str(e)}")

        return False

    def generate_hourly_report(self):
        """Generate and log hourly summary"""
        now = datetime.now()
        if now - self.last_hourly_report >= timedelta(hours=1):
            trades_this_hour = self.total_trades - self.hourly_trades_start
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

            self.logger.info("=" * 60)
            self.logger.info("HOURLY SUMMARY")
            self.logger.info(f"Trades this hour: {trades_this_hour}")
            self.logger.info(f"Total trades: {self.total_trades}")
            self.logger.info(f"Win rate: {win_rate:.1f}%")
            self.logger.info(f"Total P&L: ${self.cumulative_pnl:+.2f}")
            self.logger.info("=" * 60)

            self.last_hourly_report = now
            self.hourly_trades_start = self.total_trades

    def generate_daily_report(self):
        """Generate and log daily summary"""
        now = datetime.now()
        if now - self.last_daily_report >= timedelta(days=1):
            trades_today = self.total_trades - self.daily_trades_start
            cycles_completed = self.total_trades // 2
            avg_profit_per_cycle = (self.cumulative_pnl / cycles_completed) if cycles_completed > 0 else 0
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

            self.logger.info("=" * 60)
            self.logger.info("DAILY SUMMARY")
            self.logger.info(f"Trades today: {trades_today}")
            self.logger.info(f"Total cycles completed: {cycles_completed}")
            self.logger.info(f"Average profit per cycle: ${avg_profit_per_cycle:+.2f}")
            self.logger.info(f"Win rate: {win_rate:.1f}%")
            self.logger.info(f"Total P&L: ${self.cumulative_pnl:+.2f}")
            self.logger.info("=" * 60)

            self.last_daily_report = now
            self.daily_trades_start = self.total_trades

    def get_status(self) -> Dict[str, Any]:
        """
        Get current bot status

        Returns:
            Status dictionary
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        cycles = self.total_trades // 2

        current_price = self.client.get_current_price(self.market)
        position = self.client.get_position(self.market)

        # Determine entry price based on active position
        entry_price = None
        if self.long_position and self.long_entry_price:
            entry_price = self.long_entry_price
        elif self.short_position and self.short_entry_price:
            entry_price = self.short_entry_price

        status = {
            'state': self.bot_state,
            'is_running': self.is_running,
            'current_price': current_price,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'cumulative_pnl': self.cumulative_pnl,
            'cycles_completed': cycles,
            'has_position': position is not None,
            'position': position,
            'entry_price': entry_price,
            'long_position': self.long_position,
            'short_position': self.short_position,
            'recent_trades': self.trades[-10:] if len(self.trades) > 0 else []
        }

        # Add error message if in error state
        if self.bot_state == "error" and self.error_message:
            status['error'] = self.error_message

        return status

    def run(self):
        """Main trading loop"""
        print(f"[DEBUG] run() called. State: {self.bot_state}, Running: {self.is_running}")

        if not self.initialize():
            print(f"[DEBUG] initialize() failed!")
            self.logger.error("Initialization failed. Exiting.")
            self.is_running = False
            # bot_state already set to "error" in initialize()
            return

        # Set running state
        self.is_running = True
        self.bot_state = "running"
        print(f"[DEBUG] State set to running. State: {self.bot_state}, Running: {self.is_running}")

        self.logger.info("🚀 Bot started. Monitoring price...")

        check_interval = self.config['monitoring']['check_interval_seconds']

        try:
            while self.is_running:
                # Check price and trade
                if not self.check_price_and_trade():
                    self.logger.warning("Trading stopped due to safety limits")
                    break

                # Generate reports
                if self.config['reporting']['hourly_summary']:
                    self.generate_hourly_report()

                if self.config['reporting']['daily_summary']:
                    self.generate_daily_report()

                # Wait for next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("\n⚠️  Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self.bot_state = "error"
        finally:
            self._shutdown()

    def stop(self):
        """Stop the bot"""
        self.is_running = False
        self.bot_state = "stopped"

    def pause(self):
        """Pause the bot"""
        self.bot_state = "paused"

    def resume(self):
        """Resume the bot"""
        if self.bot_state == "paused":
            self.bot_state = "running"

    def _shutdown(self):
        """Cleanup and final reporting"""
        self.logger.info("=" * 60)
        self.logger.info("BOT SHUTDOWN - FINAL REPORT")
        self.logger.info("=" * 60)

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        cycles_completed = self.total_trades // 2

        self.logger.info(f"Total trades executed: {self.total_trades}")
        self.logger.info(f"Total cycles completed: {cycles_completed}")
        self.logger.info(f"Winning trades: {self.winning_trades}")
        self.logger.info(f"Win rate: {win_rate:.1f}%")
        self.logger.info(f"Final P&L: ${self.cumulative_pnl:+.2f}")

        # Check for open position
        position = self.client.get_position(self.market)
        if position:
            self.logger.warning(f"Open position: {position['side']} {position['size']} @ ${position['entry_price']:.2f}")
            self.logger.warning(f"Unrealized P&L: ${position['unrealized_pnl']:+.2f}")

        self.logger.info("=" * 60)
