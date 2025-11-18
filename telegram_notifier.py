"""
Telegram Bot for Grid Trading Bot Notifications
Sends trade alerts, status updates, and provides interactive commands
"""

import os
import asyncio
from typing import Optional, Any
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import logging
from datetime import datetime
import requests
import json


class TelegramNotifier:
    """Handles Telegram notifications and bot commands"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None, logger=None):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Your Telegram chat ID
            logger: Logger instance
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.logger = logger or logging.getLogger(__name__)
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.enabled = False
        self.trader = None  # Will be set by grid trader

        if self.bot_token and self.chat_id:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
            self.logger.info("Telegram notifier initialized")
        else:
            self.logger.warning("Telegram credentials not found. Notifications disabled.")

    async def start_bot(self, trader):
        """
        Start the Telegram bot with command handlers

        Args:
            trader: Reference to the grid trader instance
        """
        if not self.enabled:
            return

        self.trader = trader

        # Create application
        self.application = Application.builder().token(self.bot_token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("pnl", self._cmd_pnl))
        self.application.add_handler(CommandHandler("position", self._cmd_position))
        self.application.add_handler(CommandHandler("stats", self._cmd_stats))
        self.application.add_handler(CommandHandler("stopbot", self._cmd_stopbot))
        self.application.add_handler(CommandHandler("startbot", self._cmd_startbot))
        self.application.add_handler(CommandHandler("restart", self._cmd_restart))
        self.application.add_handler(CommandHandler("instruments", self._cmd_instruments))
        self.application.add_handler(CommandHandler("help", self._cmd_help))

        # Start polling in background
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        self.logger.info("Telegram bot started and listening for commands")

        # Send startup message
        await self.send_message("🤖 Grid Trading Bot Started!\n\nUse /help to see available commands.")

    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Telegram bot stopped")

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram

        Args:
            message: Message text
            parse_mode: Message formatting (HTML or Markdown)

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False

    # Notification methods

    async def notify_trade(self, side: str, quantity: float, price: float, market: str):
        """Notify about trade execution"""
        emoji = "🟢" if side.lower() == "buy" else "🔴"
        message = (
            f"{emoji} <b>{side.upper()} ORDER EXECUTED</b>\n\n"
            f"Market: {market}\n"
            f"Quantity: {quantity}\n"
            f"Price: ${price:.4f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await self.send_message(message)

    async def notify_position_update(self, position_size: float, entry_price: float,
                                     current_price: float, pnl: float, pnl_percentage: float):
        """Notify about position updates"""
        emoji = "📈" if pnl >= 0 else "📉"
        pnl_sign = "+" if pnl >= 0 else ""
        message = (
            f"{emoji} <b>POSITION UPDATE</b>\n\n"
            f"Size: {position_size}\n"
            f"Entry: ${entry_price:.4f}\n"
            f"Current: ${current_price:.4f}\n"
            f"P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_percentage:.2f}%)\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(message)

    async def notify_error(self, error_msg: str):
        """Notify about errors"""
        message = (
            f"⚠️ <b>ERROR</b>\n\n"
            f"{error_msg}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await self.send_message(message)

    async def notify_daily_summary(self, trades: int, pnl: float, win_rate: float):
        """Send daily summary"""
        emoji = "✅" if pnl >= 0 else "❌"
        pnl_sign = "+" if pnl >= 0 else ""
        message = (
            f"📊 <b>DAILY SUMMARY</b>\n\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"Trades: {trades}\n"
            f"P&L: {pnl_sign}${pnl:.2f} {emoji}\n"
            f"Win Rate: {win_rate:.1f}%\n"
        )
        await self.send_message(message)

    async def notify_bot_stopped(self, reason: str = "Manual stop"):
        """Notify when bot stops"""
        message = (
            f"🛑 <b>BOT STOPPED</b>\n\n"
            f"Reason: {reason}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await self.send_message(message)

    # Command handlers

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_msg = (
            "👋 <b>Welcome to Grid Trading Bot!</b>\n\n"
            "I'll send you notifications about:\n"
            "• Trade executions\n"
            "• Position updates\n"
            "• P&L changes\n"
            "• Errors and alerts\n\n"
            "Use /help to see all commands."
        )
        await update.message.reply_text(welcome_msg, parse_mode="HTML")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        try:
            status = "🟢 Running" if self.trader.bot_state == "running" else "🔴 Stopped"
            message = (
                f"<b>BOT STATUS</b>\n\n"
                f"Status: {status}\n"
                f"Market: {self.trader.market}\n"
                f"Direction: {self.trader.trade_direction.upper()}\n"
                f"Leverage: {self.trader.leverage}x\n"
                f"Buy Level: ${self.trader.buy_level:.2f}\n"
                f"Sell Level: ${self.trader.sell_level:.2f}\n"
            )
            await update.message.reply_text(message, parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")

    async def _cmd_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl command"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        try:
            pnl = self.trader.cumulative_pnl
            trades = self.trader.total_trades
            pnl_sign = "+" if pnl >= 0 else ""
            emoji = "📈" if pnl >= 0 else "📉"

            message = (
                f"{emoji} <b>PROFIT & LOSS</b>\n\n"
                f"Total P&L: {pnl_sign}${pnl:.2f}\n"
                f"Total Trades: {trades}\n"
                f"Avg P&L/Trade: {pnl_sign}${(pnl/trades if trades > 0 else 0):.2f}\n"
            )
            await update.message.reply_text(message, parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting P&L: {str(e)}")

    async def _cmd_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /position command"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        # Get current position from exchange
        try:
            position = self.trader.client.get_position(self.trader.market)
            if position and position.get('size', 0) != 0:
                size = position.get('size', 0)
                entry = position.get('entry_price', 0)
                current = self.trader.client.get_current_price(self.trader.market)

                message = (
                    f"📊 <b>CURRENT POSITION</b>\n\n"
                    f"Market: {self.trader.market}\n"
                    f"Size: {size}\n"
                    f"Entry: ${entry:.4f}\n"
                    f"Current: ${current:.4f}\n"
                )
            else:
                message = "No open position"

            await update.message.reply_text(message, parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting position: {str(e)}")

    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        try:
            win_rate = (self.trader.winning_trades / self.trader.total_trades * 100) if self.trader.total_trades > 0 else 0

            message = (
                f"📊 <b>TRADING STATISTICS</b>\n\n"
                f"Total Trades: {self.trader.total_trades}\n"
                f"Winning Trades: {self.trader.winning_trades}\n"
                f"Win Rate: {win_rate:.1f}%\n"
                f"Total P&L: ${self.trader.cumulative_pnl:.2f}\n"
                f"Grid Range: ${self.trader.sell_level - self.trader.buy_level:.2f}\n"
                f"Position Size: {self.trader.position_size}\n"
                f"Leverage: {self.trader.leverage}x\n"
            )
            await update.message.reply_text(message, parse_mode="HTML")
        except Exception as e:
            await update.message.reply_text(f"❌ Error getting stats: {str(e)}")

    async def _cmd_stopbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stopbot command - stops the trading bot"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        if self.trader.bot_state != "running":
            await update.message.reply_text(f"ℹ️ Bot is already stopped (state: {self.trader.bot_state})")
            return

        try:
            await update.message.reply_text("🛑 Stopping trading bot...")
            self.trader.stop()
            await update.message.reply_text("✅ Trading bot stopped successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error stopping bot: {str(e)}")

    async def _cmd_startbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /startbot command - starts the trading bot"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        if self.trader.bot_state == "running":
            await update.message.reply_text("ℹ️ Bot is already running!")
            return

        try:
            await update.message.reply_text("🚀 Starting trading bot...")
            # Start the bot in a new thread
            import threading
            bot_thread = threading.Thread(target=self.trader.run, daemon=True)
            bot_thread.start()
            await asyncio.sleep(2)  # Wait for initialization
            await update.message.reply_text("✅ Trading bot started successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error starting bot: {str(e)}")

    async def _cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command - restarts the trading bot"""
        if not self.trader:
            await update.message.reply_text("❌ Trader not initialized")
            return

        try:
            await update.message.reply_text("🔄 Restarting trading bot...")

            # Stop if running
            if self.trader.bot_state == "running":
                self.trader.stop()
                await asyncio.sleep(2)

            # Start again
            import threading
            bot_thread = threading.Thread(target=self.trader.run, daemon=True)
            bot_thread.start()
            await asyncio.sleep(2)

            await update.message.reply_text("✅ Trading bot restarted successfully!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error restarting bot: {str(e)}")

    async def _cmd_instruments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /instruments command - fetch CoinDCX active USDT instruments"""
        try:
            await update.message.reply_text("🔄 Fetching active USDT instruments from CoinDCX...")

            # Fetch active instruments from CoinDCX API
            url = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments?margin_currency_short_name[]=USDT"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                await update.message.reply_text(f"❌ Error fetching instruments: HTTP {response.status_code}")
                return

            instruments = response.json()

            if not instruments:
                await update.message.reply_text("❌ No active instruments found")
                return

            # Format the response - show first 20 instruments and total count
            total_count = len(instruments)
            display_limit = 20

            message = f"📊 <b>CoinDCX Active USDT Instruments</b>\n\n"
            message += f"Total: <b>{total_count}</b> instruments\n\n"
            message += f"<b>First {min(display_limit, total_count)} instruments:</b>\n"

            for i, instrument in enumerate(instruments[:display_limit], 1):
                message += f"{i}. <code>{instrument}</code>\n"

            if total_count > display_limit:
                message += f"\n... and {total_count - display_limit} more"

            # Send the message
            await update.message.reply_text(message, parse_mode="HTML")

            # Optionally send the full list as a file for easy reference
            if total_count > display_limit:
                # Create a formatted text file
                file_content = "CoinDCX Active USDT Instruments\n"
                file_content += "=" * 40 + "\n\n"
                for instrument in instruments:
                    file_content += f"{instrument}\n"

                # Send as document
                from io import BytesIO
                file_bytes = BytesIO(file_content.encode('utf-8'))
                file_bytes.name = f"coindcx_instruments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                await update.message.reply_document(
                    document=file_bytes,
                    filename=file_bytes.name,
                    caption=f"📄 Complete list of {total_count} active USDT instruments"
                )

        except requests.RequestException as e:
            await update.message.reply_text(f"❌ Network error: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            self.logger.error(f"Error in /instruments command: {e}")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = (
            "<b>📋 AVAILABLE COMMANDS</b>\n\n"
            "<b>🎮 Bot Control:</b>\n"
            "/startbot - Start the trading bot\n"
            "/stopbot - Stop the trading bot\n"
            "/restart - Restart the trading bot\n\n"
            "<b>📊 Information:</b>\n"
            "/status - Get bot status\n"
            "/pnl - View profit & loss\n"
            "/position - Check current position\n"
            "/stats - Trading statistics\n"
            "/instruments - View active USDT instruments\n\n"
            "<b>ℹ️ Other:</b>\n"
            "/start - Welcome message\n"
            "/help - Show this message\n"
        )
        await update.message.reply_text(help_msg, parse_mode="HTML")


# Synchronous wrapper functions for backward compatibility
def send_telegram_notification(message: str, notifier: Optional[TelegramNotifier] = None):
    """Synchronous wrapper to send Telegram message"""
    if notifier and notifier.enabled:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                asyncio.create_task(notifier.send_message(message))
            else:
                # If no loop, run synchronously
                loop.run_until_complete(notifier.send_message(message))
        except Exception as e:
            if notifier.logger:
                notifier.logger.error(f"Error sending Telegram notification: {e}")
