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

        # Safety parameters
        self.max_loss = config['safety']['max_cumulative_loss']
        self.support_level = config['safety']['support_level']
        self.resistance_level = config['safety']['resistance_level']
        self.trading_range_min = config['safety']['trading_range_min']
        self.trading_range_max = config['safety']['trading_range_max']

        # State tracking
        self.current_position = None
        self.entry_price = None
        self.trades = []
        self.cumulative_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.is_running = True
        self.bot_state = "initializing"

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
            self.logger.error("Failed to connect to CoinDCX API")
            self.bot_state = "error"
            return False

        # Set leverage
        if not self.client.set_leverage(self.market, self.leverage):
            self.logger.warning("Could not set leverage, continuing anyway")

        # Display configuration
        self.logger.info(f"Trading Market: {self.market}")
        self.logger.info(f"Buy Level: ${self.buy_level:.2f}")
        self.logger.info(f"Sell Level: ${self.sell_level:.2f}")
        self.logger.info(f"Grid Range: ${self.sell_level - self.buy_level:.2f}")
        self.logger.info(f"Position Size: {self.position_size} SOL")
        self.logger.info(f"Leverage: {self.leverage}x")
        self.logger.info(f"Order Type: {self.order_type}")
        self.logger.info(f"Max Loss: ${self.max_loss:.2f}")
        self.logger.info(f"Trading Range: ${self.trading_range_min:.2f} - ${self.trading_range_max:.2f}")
        self.logger.info("=" * 60)

        # Check for existing position
        position = self.client.get_position(self.market)
        if position:
            self.logger.warning(f"Existing position detected: {position['side']} {position['size']} @ ${position['entry_price']:.2f}")
            self.current_position = position
            self.entry_price = position['entry_price']

        self.bot_state = "running"
        return True

    def check_price_and_trade(self) -> bool:
        """
        Check current price and execute trades if conditions are met

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

        # Check current position
        position = self.client.get_position(self.market)
        has_position = position is not None and position['size'] > 0

        # Execute buy logic
        if current_price <= self.buy_level and not has_position:
            if self._execute_buy(current_price):
                self.total_trades += 1

        # Execute sell logic
        elif current_price >= self.sell_level and has_position:
            if self._execute_sell(current_price):
                self.total_trades += 1

        # Check if cumulative loss exceeds limit
        if self.cumulative_pnl <= self.max_loss:
            self.logger.alert(f"Cumulative loss ${self.cumulative_pnl:.2f} exceeds limit ${self.max_loss:.2f}. STOPPING TRADING.")
            self.bot_state = "stopped"
            return False

        return True

    def _execute_buy(self, current_price: float) -> bool:
        """
        Execute buy order

        Args:
            current_price: Current market price

        Returns:
            True if order executed successfully
        """
        try:
            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'buy', self.position_size)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'buy', self.position_size, self.buy_level)
                execution_price = self.buy_level

            if order:
                self.entry_price = execution_price
                self.current_position = {'side': 'long', 'size': self.position_size, 'entry_price': execution_price}
                self.logger.trade_execution('BUY', self.position_size, execution_price)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'BUY',
                    'price': execution_price,
                    'quantity': self.position_size,
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
            # Place order
            if self.order_type == 'market':
                order = self.client.place_market_order(self.market, 'sell', self.position_size)
                execution_price = current_price
            else:  # limit order
                order = self.client.place_limit_order(self.market, 'sell', self.position_size, self.sell_level)
                execution_price = self.sell_level

            if order and self.entry_price:
                # Calculate profit
                profit = (execution_price - self.entry_price) * self.position_size
                self.cumulative_pnl += profit

                # Update statistics
                if profit > 0:
                    self.winning_trades += 1

                self.logger.trade_execution('SELL', self.position_size, execution_price, profit)

                # Record trade
                self.trades.append({
                    'timestamp': datetime.now(),
                    'type': 'SELL',
                    'price': execution_price,
                    'quantity': self.position_size,
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

        return {
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
            'entry_price': self.entry_price,
            'recent_trades': self.trades[-10:] if len(self.trades) > 0 else []
        }

    def run(self):
        """Main trading loop"""
        if not self.initialize():
            self.logger.error("Initialization failed. Exiting.")
            return

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
