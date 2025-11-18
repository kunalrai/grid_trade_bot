"""
Standalone Telegram Bot for Cryptocurrency Technical Analysis
Provides real-time market analysis and trading signals for 15+ cryptocurrencies
Uses CoinDCX market data with RSI, MACD, and EMA indicators
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
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StandaloneTelegramBot:
    """Standalone Telegram bot for cryptocurrency technical analysis"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.application = None
        self.analyzer = TechnicalAnalyzer()  # Technical analysis module

    async def start(self):
        """Start the Telegram bot"""
        self.application = Application.builder().token(self.bot_token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("price", self._cmd_price))
        self.application.add_handler(CommandHandler("instruments", self._cmd_instruments))

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

        # Send startup message
        bot = Bot(token=self.bot_token)
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text="🤖 <b>Crypto Technical Analysis Bot Started!</b>\n\n📈 Ready to provide market analysis and trading signals.\n\nUse /help to see available commands.",
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
            "👋 <b>Welcome to Crypto Technical Analysis Bot!</b>\n\n"
            "I provide real-time technical analysis for cryptocurrency markets.\n\n"
            "<b>What I can do:</b>\n"
            "• Real-time price data from CoinDCX\n"
            "• Technical analysis with RSI, MACD, EMA indicators\n"
            "• Multi-timeframe market scanning\n"
            "• Trading signal detection across 15+ coins\n"
            "• View active USDT trading instruments\n\n"
            "Use /help to see all commands."
        )
        await update.message.reply_text(welcome_msg, parse_mode="HTML")

    async def _cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command - fetch price from CoinDCX futures market"""
        if not context.args:
            await update.message.reply_text(
                "Usage: /price &lt;COIN&gt;\n"
                "Example: /price BTC\n"
                "Example: /price SOL\n\n"
                "Available: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, LTC, ATOM, ZEC",
                parse_mode="HTML"
            )
            return

        coin = context.args[0].upper()
        market = f"B-{coin}_USDT"

        try:
            # Get real-time price from v3 order book (most accurate)
            orderbook_url = f'https://public.coindcx.com/market_data/v3/orderbook/{market}-futures/20'
            response = requests.get(orderbook_url, timeout=10)
            response.raise_for_status()
            orderbook = response.json()

            # Get best bid and ask
            bids = orderbook.get('bids', {})
            asks = orderbook.get('asks', {})

            if not bids or not asks:
                await update.message.reply_text(f"❌ No order book data for {coin}")
                return

            # Sort to get best prices
            bid_prices = sorted([float(p) for p in bids.keys()], reverse=True)
            ask_prices = sorted([float(p) for p in asks.keys()])

            best_bid = bid_prices[0]
            best_ask = ask_prices[0]
            mid_price = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            spread_pct = (spread / mid_price * 100) if mid_price > 0 else 0

            # Calculate total bid/ask volume for top 5 levels
            bid_volume = sum(float(bids[str(p)]) for p in bid_prices[:5])
            ask_volume = sum(float(asks[str(p)]) for p in ask_prices[:5])

            # Get 24h data from 1d candle for high/low/open
            daily_analysis = self.analyzer.analyze_market(market, '1d')

            if daily_analysis:
                high = daily_analysis['price']['high']
                low = daily_analysis['price']['low']
                open_price = daily_analysis['price']['open']
                change_pct = ((mid_price - open_price) / open_price * 100) if open_price > 0 else 0
            else:
                high = mid_price
                low = mid_price
                change_pct = 0

            # Timestamp from orderbook
            timestamp = orderbook.get('ts', 0)
            data_time = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S') if timestamp else datetime.now().strftime('%H:%M:%S')

            message = (
                f"💰 <b>FUTURES MARKET PRICE</b>\n\n"
                f"Market: <code>{coin}/USDT-PERP</code>\n"
                f"Price: <b>${mid_price:.2f}</b>\n"
                f"Bid: ${best_bid:.2f} | Ask: ${best_ask:.2f}\n"
                f"Spread: ${spread:.2f} ({spread_pct:.3f}%)\n\n"
                f"24h High: ${high:.2f}\n"
                f"24h Low: ${low:.2f}\n"
                f"24h Change: {change_pct:+.2f}%\n\n"
                f"Top 5 Liquidity:\n"
                f"Bid: {bid_volume:.2f} {coin} | Ask: {ask_volume:.2f} {coin}\n\n"
                f"⏰ {data_time}"
            )
            await update.message.reply_text(message, parse_mode="HTML")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

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

    async def _cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - detailed technical analysis for a specific coin"""
        # Usage: /analyze BTC or /analyze SOL 4h
        if not context.args:
            await update.message.reply_text(
                "Usage: /analyze <COIN> [TIMEFRAME]\n"
                "Example: /analyze BTC\n"
                "Example: /analyze ETH 4h\n\n"
                "Available: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, LTC, ATOM, ZEC\n"
                "Timeframes: 5m, 15m, 1h, 2h, 4h, 1d (default: 5m)"
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
        """Handle /scan command - scan multiple coins on multiple timeframes"""
        timeframes = context.args if context.args else ['5m', '15m', '1h', '2h', '4h', '1d']

        await update.message.reply_text(f"🔍 Scanning major coins on {', '.join(timeframes)} timeframes...")

        try:
            markets = [
                'B-BTC_USDT',   # Bitcoin
                'B-ETH_USDT',   # Ethereum
                'B-SOL_USDT',   # Solana
                'B-BNB_USDT',   # Binance Coin
                'B-XRP_USDT',   # Ripple
                'B-ADA_USDT',   # Cardano
                'B-DOGE_USDT',  # Dogecoin
                'B-MATIC_USDT', # Polygon
                'B-DOT_USDT',   # Polkadot
                'B-AVAX_USDT',  # Avalanche
                'B-LINK_USDT',  # Chainlink
                'B-UNI_USDT',   # Uniswap
                'B-LTC_USDT',   # Litecoin
                'B-ATOM_USDT',  # Cosmos
                'B-ZEC_USDT'    # Zcash
            ]
            results = self.analyzer.scan_multiple_markets(markets, timeframes)

            message = f"<b>📊 MARKET SCAN RESULTS</b>\n"
            message += f"Timeframes: {', '.join(timeframes)}\n"
            message += "━━━━━━━━━━━━━━━━━━\n\n"

            for market, intervals in results.items():
                coin = market.replace('B-', '').replace('_USDT', '')

                # Get price from first available timeframe
                price = 0
                for tf_data in intervals.values():
                    if tf_data.get('price'):
                        price = tf_data['price'].get('current', 0)
                        break

                # Check for crosses in any timeframe
                cross_marker = ""
                for tf_data in intervals.values():
                    cross = tf_data.get('ema', {}).get('cross', 'none')
                    if cross == 'golden_cross':
                        cross_marker = " ✨"
                        break
                    elif cross == 'death_cross':
                        cross_marker = " ☠️"
                        break

                message += f"<b>{coin}</b> ${price:.2f}{cross_marker}\n"

                # Show signal for each timeframe
                for tf in timeframes:
                    tf_data = intervals.get(tf, {})
                    signal = tf_data.get('signal', 'N/A')
                    emoji = '🟢' if 'buy' in signal else '🔴' if 'sell' in signal else '⚪'
                    message += f"{tf}: {emoji} {signal.replace('_', ' ').title()}\n"

                message += "\n"

            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"

            await update.message.reply_text(message, parse_mode="HTML")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            logger.error(f"Error in scan command: {e}")

    async def _cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command - show only actionable buy/sell signals"""
        await update.message.reply_text("🎯 Finding trading signals across 15 coins and 6 timeframes...")

        try:
            markets = [
                'B-BTC_USDT',   # Bitcoin
                'B-ETH_USDT',   # Ethereum
                'B-SOL_USDT',   # Solana
                'B-BNB_USDT',   # Binance Coin
                'B-XRP_USDT',   # Ripple
                'B-ADA_USDT',   # Cardano
                'B-DOGE_USDT',  # Dogecoin
                'B-MATIC_USDT', # Polygon
                'B-DOT_USDT',   # Polkadot
                'B-AVAX_USDT',  # Avalanche
                'B-LINK_USDT',  # Chainlink
                'B-UNI_USDT',   # Uniswap
                'B-LTC_USDT',   # Litecoin
                'B-ATOM_USDT',  # Cosmos
                'B-ZEC_USDT'    # Zcash
            ]
            timeframes = ['5m', '15m', '1h', '2h', '4h', '1d']
            signals = self.analyzer.get_trading_signals(markets, timeframes)

            message = "<b>🎯 TRADING SIGNALS</b>\n"
            message += "━━━━━━━━━━━━━━━━━━\n\n"

            has_signals = False

            # Strong Buy signals
            if signals['strong_buy']:
                has_signals = True
                message += "<b>🟢🟢 STRONG BUY:</b>\n"
                for item in signals['strong_buy']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    # Get price from first available timeframe
                    price = 0
                    for tf_data in item['timeframe_data'].values():
                        if tf_data.get('price'):
                            price = tf_data['price'].get('current', 0)
                            break
                    conf_count = item['confirmation_count']
                    total = item['total_timeframes']
                    message += f"• {coin} ${price:.2f} ({conf_count}/{total} TF)\n"
                message += "\n"

            # Buy signals
            if signals['buy']:
                has_signals = True
                message += "<b>🟢 BUY:</b>\n"
                for item in signals['buy']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = 0
                    for tf_data in item['timeframe_data'].values():
                        if tf_data.get('price'):
                            price = tf_data['price'].get('current', 0)
                            break
                    conf_count = item['confirmation_count']
                    total = item['total_timeframes']
                    message += f"• {coin} ${price:.2f} ({conf_count}/{total} TF)\n"
                message += "\n"

            # Strong Sell signals
            if signals['strong_sell']:
                has_signals = True
                message += "<b>🔴🔴 STRONG SELL:</b>\n"
                for item in signals['strong_sell']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = 0
                    for tf_data in item['timeframe_data'].values():
                        if tf_data.get('price'):
                            price = tf_data['price'].get('current', 0)
                            break
                    conf_count = item['confirmation_count']
                    total = item['total_timeframes']
                    message += f"• {coin} ${price:.2f} ({conf_count}/{total} TF)\n"
                message += "\n"

            # Sell signals
            if signals['sell']:
                has_signals = True
                message += "<b>🔴 SELL:</b>\n"
                for item in signals['sell']:
                    coin = item['market'].replace('B-', '').replace('_USDT', '')
                    price = 0
                    for tf_data in item['timeframe_data'].values():
                        if tf_data.get('price'):
                            price = tf_data['price'].get('current', 0)
                            break
                    conf_count = item['confirmation_count']
                    total = item['total_timeframes']
                    message += f"• {coin} ${price:.2f} ({conf_count}/{total} TF)\n"
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
            "<b>📊 Market Data:</b>\n"
            "/price [market] - Get current price\n"
            "/instruments - View active USDT instruments\n\n"
            "<b>📈 Technical Analysis:</b>\n"
            "/analyze &lt;COIN&gt; [TF] - Detailed analysis (15+ coins)\n"
            "/scan [TF...] - Scan 15 coins (default: 6 timeframes)\n"
            "/signals - Get signals with confirmation counts\n\n"
            "<b>ℹ️ Other:</b>\n"
            "/start - Welcome message\n"
            "/help - Show this message\n\n"
            "<b>Supported Coins:</b>\n"
            "BTC, ETH, SOL, BNB, XRP, ADA, DOGE, MATIC, DOT, AVAX, LINK, UNI, LTC, ATOM, ZEC\n\n"
            "<b>Timeframes:</b>\n"
            "5m, 15m, 1h, 2h, 4h, 1d"
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
    logger.info("CRYPTO TECHNICAL ANALYSIS TELEGRAM BOT")
    logger.info("=" * 60)

    bot = StandaloneTelegramBot(TELEGRAM_BOT_TOKEN)

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
