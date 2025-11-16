"""
Logging module for the SOL/USDT Grid Trading Bot
"""
import logging
import os
from datetime import datetime
from typing import Optional


class TradingLogger:
    """Handles all logging for the trading bot"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._setup_logger()

    def _setup_logger(self):
        """Set up logging configuration"""
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Create logger
        self.logger = logging.getLogger("GridTradingBot")
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)

        # File handler
        log_file = os.path.join(
            self.log_dir,
            f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def trade_execution(self, side: str, quantity: float, price: float, profit: Optional[float] = None):
        """Log trade execution"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if profit is not None:
            message = f"[{timestamp}] {side.upper()} {quantity} SOL at ${price:.2f} | Profit: ${profit:.2f}"
        else:
            message = f"[{timestamp}] {side.upper()} {quantity} SOL at ${price:.2f}"
        self.logger.info(message)

    def status_update(self, trades: int, win_rate: float, total_pnl: float):
        """Log status update"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"[{timestamp}] [Status] Trades: {trades} | Win Rate: {win_rate:.1f}% | Total P&L: ${total_pnl:+.2f}"
        self.logger.info(message)

    def alert(self, message: str):
        """Log alert message"""
        self.logger.warning(f"⚠️  ALERT: {message}")
