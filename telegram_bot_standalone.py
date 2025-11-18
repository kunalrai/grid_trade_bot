"""
Standalone Telegram Bot for Grid Trading Bot
Can run independently to monitor and control the trading bot via API
Includes Technical Analysis features for BTC, ETH, SOL, ZEC
"""
import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from datetime import datetime
import logging
from technical_analysis import TechnicalAnalyzer

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StandaloneTelegramBot:
    """Standalone Telegram bot that communicates with the trading bot via API"""

    def __init__(self, bot_token: str, api_url: str):
        self.bot_token = bot_token
        self.api_url = api_url
        self.application = None
        self.analyzer = TechnicalAnalyzer()  # Technical analysis module

    def _api_call(self, endpoint: str, method: str = 'GET') -> dict:
        """Make API call to the trading bot server"""
        try:
            url = f"{self.api_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, timeout=10)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            return {'error': str(e)}

    async def start(self):
        """Start the Telegram bot"""
        self.application = Application.builder().token(self.bot_token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("price", self._cmd_price))
        self.application.add_handler(CommandHandler("pnl", self._cmd_pnl))
        self.application.add_handler(CommandHandler("stats", self._cmd_stats))
        self.application.add_handler(CommandHandler("startbot", self._cmd_startbot))
        self.application.add_handler(CommandHandler("stopbot", self._cmd_stopbot))
        self.application.add_handler(CommandHandler("instruments", self._cmd_instruments))
        self.application.add_handler(CommandHandler("health", self._cmd_health))

        # Technical Analysis commands
        self.application.add_handler(CommandHandler("analyze", self._cmd_analyze))
        self.application.add_handler(CommandHandler("scan", self._cmd_scan))
        self.application.add_handler(CommandHandler("signals", self._cmd_signals))

        self.application.add_handler(CommandHandler("help", self._cmd_help))

        # Start polling
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("Telegram bot started and listening for commands")
        logger.info(f"API endpoint: {self.api_url}")

        # Send startup message
        bot = Bot(token=self.bot_token)
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="🤖 <b>Standalone Telegram Bot Started!</b>\n\nUse /help to see available commands.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")

    async def stop(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")

    # Command handlers

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_msg = (
            "👋 <b>Welcome to Grid Trading Bot Controller!</b>\n\n"
            "I'm a standalone bot that connects to your trading bot API.\n\n"
            "<b>What I can do:</b>\n"
            "• Check bot status and prices\n"
            "• Start/stop the trading bot\n"
            "• View P&L and statistics\n"
            "• Monitor health status\n\n"
            f"<b>API Endpoint:</b> {self.api_url}\n\n"
            "Use /help to see all commands."
        )
        await update.message.reply_text(welcome_msg, parse_mode="HTML")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await update.message.reply_text("⏳ Fetching bot status...")

        result = self._api_call('/api/bot/status')

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
            return

        status = "🟢 Running" if result.get('is_running') else "🔴 Stopped"
        state = result.get('state', 'unknown').upper()

        message = (
            f"<b>BOT STATUS</b>\n\n"
            f"Status: {status}\n"
            f"State: {state}\n"
        )

        if result.get('is_running'):
            message += (
                f"Total Trades: {result.get('total_trades', 0)}\n"
                f"P&L: ${result.get('cumulative_pnl', 0):.2f}\n"
                f"Win Rate: {result.get('win_rate', 0):.1f}%\n"
            )

        await update.message.reply_text(message, parse_mode="HTML")

    async def _cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command - works without authentication"""
        market = context.args[0] if context.args else None

        endpoint = '/api/market/price'
        if market:
            endpoint += f'?market={market}'

        result = self._api_call(endpoint)

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
            return

        message = (
            f"💰 <b>MARKET PRICE</b>\n\n"
            f"Market: <code>{result.get('market')}</code>\n"
            f"Price: <b>${result.get('price'):.4f}</b>\n"
            f"Time: {datetime.fromisoformat(result.get('timestamp')).strftime('%H:%M:%S')}"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    async def _cmd_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl command"""
        result = self._api_call('/api/bot/status')

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
            return

        pnl = result.get('cumulative_pnl', 0)
        trades = result.get('total_trades', 0)
        pnl_sign = "+" if pnl >= 0 else ""
        emoji = "📈" if pnl >= 0 else "📉"

        message = (
            f"{emoji} <b>PROFIT & LOSS</b>\n\n"
            f"Total P&L: {pnl_sign}${pnl:.2f}\n"
            f"Total Trades: {trades}\n"
            f"Avg P&L/Trade: {pnl_sign}${(pnl/trades if trades > 0 else 0):.2f}\n"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        result = self._api_call('/api/stats')

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
            return

        message = (
            f"📊 <b>TRADING STATISTICS</b>\n\n"
            f"Total Trades: {result.get('total_trades', 0)}\n"
            f"Winning Trades: {result.get('winning_trades', 0)}\n"
            f"Losing Trades: {result.get('losing_trades', 0)}\n"
            f"Win Rate: {result.get('win_rate', 0):.1f}%\n"
            f"Total P&L: ${result.get('cumulative_pnl', 0):.2f}\n"
            f"Cycles: {result.get('cycles_completed', 0)}\n"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    async def _cmd_startbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /startbot command"""
        await update.message.reply_text("🚀 Starting trading bot...")

        result = self._api_call('/api/bot/start', method='POST')

        if 'error' in result:
            message = f"❌ Failed to start bot\n\n{result.get('error')}"
            if 'message' in result:
                message += f"\n\n💡 {result.get('message')}"
            if 'hint' in result:
                message += f"\n\n{result.get('hint')}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("✅ Trading bot started successfully!")

    async def _cmd_stopbot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stopbot command"""
        await update.message.reply_text("🛑 Stopping trading bot...")

        result = self._api_call('/api/bot/stop', method='POST')

        if 'error' in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
        else:
            await update.message.reply_text("✅ Trading bot stopped successfully!")

    async def _cmd_instruments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /instruments command - fetch CoinDCX active USDT instruments"""
        try:
            await update.message.reply_text("🔄 Fetching active USDT instruments from CoinDCX...")

            # Fetch directly from CoinDCX public API (no auth needed)
            url = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments?margin_currency_short_name[]=USDT"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                await update.message.reply_text(f"❌ Error fetching instruments: HTTP {response.status_code}")
                return

            instruments = response.json()

            if not instruments:
                await update.message.reply_text("❌ No active instruments found")
                return

            # Format the response
            total_count = len(instruments)
            display_limit = 20

            message = f"📊 <b>CoinDCX Active USDT Instruments</b>\n\n"
            message += f"Total: <b>{total_count}</b> instruments\n\n"
            message += f"<b>First {min(display_limit, total_count)} instruments:</b>\n"

            for i, instrument in enumerate(instruments[:display_limit], 1):
                message += f"{i}. <code>{instrument}</code>\n"

            if total_count > display_limit:
                message += f"\n... and {total_count - display_limit} more"

            await update.message.reply_text(message, parse_mode="HTML")

            # Send full list as file if there are many
            if total_count > display_limit:
                file_content = "CoinDCX Active USDT Instruments\n"
                file_content += "=" * 40 + "\n\n"
                for instrument in instruments:
                    file_content += f"{instrument}\n"

                from io import BytesIO
                file_bytes = BytesIO(file_content.encode('utf-8'))
                file_bytes.name = f"coindcx_instruments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

                await update.message.reply_document(
                    document=file_bytes,
                    filename=file_bytes.name,
                    caption=f"📄 Complete list of {total_count} active USDT instruments"
                )

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def _cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        result = self._api_call('/api/health')

        if 'error' in result:
            await update.message.reply_text(f"❌ API is down: {result['error']}")
            return

        status_emoji = "✅" if result.get('status') == 'ok' else "❌"
        bot_running = "🟢 Running" if result.get('bot_running') else "🔴 Stopped"

        message = (
            f"{status_emoji} <b>HEALTH CHECK</b>\n\n"
            f"API Status: {result.get('status', 'unknown').upper()}\n"
            f"Bot: {bot_running}\n"
            f"Bot State: {result.get('bot_state', 'unknown').upper()}\n"
            f"Timestamp: {datetime.fromisoformat(result.get('timestamp')).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await update.message.reply_text(message, parse_mode="HTML")

    async def _cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - detailed technical analysis for a specific coin"""
        # Usage: /analyze BTC or /analyze SOL 4h
        if not context.args:
            await update.message.reply_text(
                "Usage: /analyze <COIN> [TIMEFRAME]\n"
                "Example: /analyze BTC\n"
                "Example: /analyze ETH 4h\n\n"
                "Available: BTC, ETH, SOL, ZEC\n"
                "Timeframes: 5m, 4h (default: 5m)"
            )
            return

        coin = context.args[0].upper()
        interval = context.args[1] if len(context.args) > 1 else '5m'

        # Convert coin to CoinDCX market format
        market = f"B-{coin}_USDT"

        await update.message.reply_text(f"🔍 Analyzing {coin}/USDT on {interval} timeframe...")

        try:
            analysis = self.analyzer.analyze_market(market, interval)

            if not analysis:
                await update.message.reply_text(f"❌ Failed to fetch data for {coin}")
                return

            # Format the message
            price = analysis['price']
            rsi = analysis['rsi']
            macd = analysis['macd']
            ema = analysis['ema']
            volume = analysis['volume']
            signal = analysis['signal']

            # Signal emoji
            signal_emoji = {
                'strong_buy': '🟢🟢',
                'buy': '🟢',
                'neutral': '⚪',
                'sell': '🔴',
                'strong_sell': '🔴🔴'
            }.get(signal, '⚪')

            message = (
                f"📊 <b>{coin}/USDT Technical Analysis</b> ({interval})\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>💰 Price:</b> ${price['current']:.2f}\n"
                f"High: ${price['high']:.2f} | Low: ${price['low']:.2f}\n\n"
                f"<b>📈 RSI (14):</b> {rsi['value']:.2f}\n"
                f"Status: {rsi['status'].upper()}\n\n"
                f"<b>📉 MACD:</b>\n"
                f"MACD: {macd['macd']:.4f}\n"
                f"Signal: {macd['signal']:.4f}\n"
                f"Histogram: {macd['histogram']:.4f} ({macd['status']})\n\n"
                f"<b>📊 EMA:</b>\n"
                f"EMA20: ${ema['ema20']:.2f}\n"
                f"EMA50: ${ema['ema50']:.2f}\n"
                f"Trend: {ema['trend'].upper()}\n"
            )

            # Add cross detection
            if ema['cross'] == 'golden_cross':
                message += "✨ <b>GOLDEN CROSS DETECTED!</b>\n"
            elif ema['cross'] == 'death_cross':
                message += "☠️ <b>DEATH CROSS DETECTED!</b>\n"

            message += (
                f"\n<b>📊 Volume:</b>\n"
                f"Current: {volume['current']:.2f}\n"
                f"Avg (20): {volume['average']:.2f}\n"
                f"Ratio: {volume['ratio']:.2f}x ({volume['status'].upper()})\n\n"
                f"<b>🎯 Signal:</b> {signal_emoji} <b>{signal.upper().replace('_', ' ')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            await update.message.reply_text(message, parse_mode="HTML")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Error in analyze command: {e}")

    async def _cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command - scan BTC, ETH, SOL, ZEC on 5m and 4h"""
        await update.message.reply_text("🔍 Scanning BTC, ETH, SOL, ZEC on 5m and 4h timeframes...")

        try:
            markets = ['B-BTC_USDT', 'B-ETH_USDT', 'B-SOL_USDT', 'B-ZEC_USDT']
            results = self.analyzer.scan_multiple_markets(markets, ['5m', '4h'])

            message = "<b>📊 MARKET SCAN RESULTS</b>\n"
            message += "━━━━━━━━━━━━━━━━━━\n\n"

            for market, intervals in results.items():
                coin = market.replace('B-', '').replace('_USDT', '')

                # Get signals for both timeframes
                tf_5m = intervals.get('5m', {})
                tf_4h = intervals.get('4h', {})

                signal_5m = tf_5m.get('signal', 'N/A')
                signal_4h = tf_4h.get('signal', 'N/A')
                price = tf_5m.get('price', {}).get('current', 0)

                # Emoji for signals
                emoji_5m = '🟢' if 'buy' in signal_5m else '🔴' if 'sell' in signal_5m else '⚪'
                emoji_4h = '🟢' if 'buy' in signal_4h else '🔴' if 'sell' in signal_4h else '⚪'

                # Special markers for crosses
                cross_5m = tf_5m.get('ema', {}).get('cross', 'none')
                cross_4h = tf_4h.get('ema', {}).get('cross', 'none')

                cross_marker = ""
                if cross_5m == 'golden_cross' or cross_4h == 'golden_cross':
                    cross_marker = " ✨"
                elif cross_5m == 'death_cross' or cross_4h == 'death_cross':
                    cross_marker = " ☠️"

                message += (
                    f"<b>{coin}</b> ${price:.2f}{cross_marker}\n"
                    f"5m: {emoji_5m} {signal_5m.replace('_', ' ').title()}\n"
                    f"4h: {emoji_4h} {signal_4h.replace('_', ' ').title()}\n\n"
                )

            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"

            await update.message.reply_text(message, parse_mode="HTML")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Error in scan command: {e}")

    async def _cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command - show only actionable buy/sell signals"""
        await update.message.reply_text("🎯 Finding trading signals...")

        try:
            markets = ['B-BTC_USDT', 'B-ETH_USDT', 'B-SOL_USDT', 'B-ZEC_USDT']
            signals = self.analyzer.get_trading_signals(markets)

            message = "<b>🎯 TRADING SIGNALS</b>\n"
            message += "━━━━━━━━━━━━━━━━━━\n\n"

            has_signals = False

            # Strong Buy signals
            if signals['strong_buy']:
                has_signals = True
                message += "<b>🟢🟢 STRONG BUY:</b>\n"
                for item in signals['strong_buy']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = item['5m'].get('price', {}).get('current', 0)
                    confirmation = item['confirmation'].replace('_', ' ').title()
                    message += f"• {coin} ${price:.2f} ({confirmation})\n"
                message += "\n"

            # Buy signals
            if signals['buy']:
                has_signals = True
                message += "<b>🟢 BUY:</b>\n"
                for item in signals['buy']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = item['5m'].get('price', {}).get('current', 0)
                    confirmation = item['confirmation'].replace('_', ' ').title()
                    message += f"• {coin} ${price:.2f} ({confirmation})\n"
                message += "\n"

            # Strong Sell signals
            if signals['strong_sell']:
                has_signals = True
                message += "<b>🔴🔴 STRONG SELL:</b>\n"
                for item in signals['strong_sell']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = item['5m'].get('price', {}).get('current', 0)
                    confirmation = item['confirmation'].replace('_', ' ').title()
                    message += f"• {coin} ${price:.2f} ({confirmation})\n"
                message += "\n"

            # Sell signals
            if signals['sell']:
                has_signals = True
                message += "<b>🔴 SELL:</b>\n"
                for item in signals['sell']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = item['5m'].get('price', {}).get('current', 0)
                    confirmation = item['confirmation'].replace('_', ' ').title()
                    message += f"• {coin} ${price:.2f} ({confirmation})\n"
                message += "\n"

            if not has_signals:
                message += "⚪ No strong signals at the moment.\n"
                message += "All markets are neutral.\n\n"

            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
            message += "\n💡 Use /analyze <COIN> for detailed analysis"

            await update.message.reply_text(message, parse_mode="HTML")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Error in signals command: {e}")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_msg = (
            "<b>📋 AVAILABLE COMMANDS</b>\n\n"
            "<b>🎮 Bot Control:</b>\n"
            "/startbot - Start the trading bot\n"
            "/stopbot - Stop the trading bot\n\n"
            "<b>📊 Information:</b>\n"
            "/status - Get bot status\n"
            "/price [market] - Get current price (no auth)\n"
            "/pnl - View profit & loss\n"
            "/stats - Trading statistics\n"
            "/instruments - View active USDT instruments (no auth)\n"
            "/health - Check API health\n\n"
            "<b>📈 Technical Analysis:</b>\n"
            "/analyze <COIN> [TF] - Detailed analysis (BTC, ETH, SOL, ZEC)\n"
            "/scan - Quick scan all coins (5m & 4h)\n"
            "/signals - Get actionable buy/sell signals\n\n"
            "<b>ℹ️ Other:</b>\n"
            "/start - Welcome message\n"
            "/help - Show this message\n\n"
            f"<b>API Endpoint:</b>\n<code>{self.api_url}</code>"
        )
        await update.message.reply_text(help_msg, parse_mode="HTML")


async def main():
    """Main function"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env file")
        return

    if not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID not set in .env file")

    logger.info("=" * 60)
    logger.info("STANDALONE TELEGRAM BOT FOR GRID TRADING")
    logger.info("=" * 60)
    logger.info(f"API Endpoint: {API_BASE_URL}")
    logger.info("=" * 60)

    bot = StandaloneTelegramBot(TELEGRAM_BOT_TOKEN, API_BASE_URL)

    try:
        await bot.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()


if __name__ == '__main__':
    asyncio.run(main())
