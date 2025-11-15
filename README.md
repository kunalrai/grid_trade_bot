# SOL/USDT Grid Trading Bot

An automated grid trading bot for SOL/USDT perpetual futures on Binance. This bot implements a simple yet effective single-grid range trading strategy.

## Strategy Overview

The bot executes a grid trading strategy with the following logic:
- **BUY** when price touches or goes below $138.00
- **SELL** when price touches or goes above $143.00
- **Grid Range**: $5.00
- Maximum 1 active position at a time (no pyramiding)

## Features

- ✅ Automated buy/sell execution based on price levels
- ✅ Real-time price monitoring (configurable interval)
- ✅ Position management with leverage support
- ✅ Safety rules and stop-loss protection
- ✅ Comprehensive logging and reporting
- ✅ Hourly and daily performance summaries
- ✅ Support/resistance breach alerts
- ✅ Cumulative P&L tracking

## Requirements

- Python 3.8 or higher
- Binance account with API access
- Sufficient USDT balance in Binance Futures wallet

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd grid_trade_bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your Binance API credentials:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

4. **Configure trading parameters**

Edit `config.json` to customize your trading settings:

```json
{
  "trading": {
    "symbol": "SOL/USDT",
    "market_type": "future",
    "buy_level": 138.00,
    "sell_level": 143.00,
    "position_size": 10,
    "leverage": 1,
    "order_type": "limit"
  },
  "safety": {
    "max_cumulative_loss": -50.0,
    "support_level": 135.0,
    "resistance_level": 146.0,
    "trading_range_min": 135.0,
    "trading_range_max": 146.0
  }
}
```

## Configuration Parameters

### Trading Settings
- `symbol`: Trading pair (default: "SOL/USDT")
- `buy_level`: Price level to execute buy orders (default: $138.00)
- `sell_level`: Price level to execute sell orders (default: $143.00)
- `position_size`: Amount of SOL per trade (default: 10)
- `leverage`: Leverage multiplier (default: 1x)
- `order_type`: "limit" or "market" (default: "limit")

### Safety Settings
- `max_cumulative_loss`: Stop trading if cumulative loss exceeds this value (default: -$50.00)
- `support_level`: Alert if price breaks below this level (default: $135.00)
- `resistance_level`: Alert if price breaks above this level (default: $146.00)
- `trading_range_min`: Pause trading if price goes below this level (default: $135.00)
- `trading_range_max`: Pause trading if price goes above this level (default: $146.00)

### Monitoring Settings
- `check_interval_seconds`: How often to check price (default: 60 seconds)

## Usage

### Start the Bot

```bash
python bot.py
```

### Testing with Binance Testnet

To test the bot without risking real funds, you can use Binance Futures Testnet:

1. Get testnet API keys from [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Update your `.env` file with testnet credentials
3. Edit `bot.py` and set `testnet=True`:
```python
client = BinanceFuturesClient(
    api_key=api_key,
    api_secret=api_secret,
    testnet=True,  # Enable testnet
    logger=logger
)
```

### Monitoring the Bot

The bot logs all activities to:
- Console output (real-time)
- Log files in `logs/` directory

Example output:
```
[2025-11-15 10:00:00] INFO: Price: $137.80 → BUY 10 SOL at $138.00
[2025-11-15 15:30:00] INFO: Price: $143.20 → SELL 10 SOL at $143.00 | Profit: $50.00
[2025-11-15 15:30:01] INFO: [Status] Trades: 2 | Win Rate: 100.0% | Total P&L: +$50.00
```

### Stopping the Bot

Press `Ctrl+C` to gracefully stop the bot. It will display a final summary before exiting.

## How It Works

### Trading Logic

1. **Initialization**
   - Connect to Binance API
   - Set leverage for SOL/USDT
   - Check for existing positions

2. **Price Monitoring**
   - Fetch current SOL/USDT price every minute (configurable)
   - Check if price is within trading range ($135-$146)

3. **Buy Execution**
   - When price ≤ $138.00 AND no position exists
   - Place buy order for configured position size
   - Record entry price

4. **Sell Execution**
   - When price ≥ $143.00 AND position exists
   - Place sell order for position size
   - Calculate and record profit/loss
   - Update cumulative P&L

5. **Safety Checks**
   - Stop trading if cumulative loss exceeds limit
   - Alert if price breaches support ($135) or resistance ($146)
   - Pause trading if price exits the $135-$146 range

6. **Reporting**
   - Hourly summary: trades, win rate, total P&L
   - Daily summary: cycles completed, average profit per cycle
   - Final report on shutdown

## Project Structure

```
grid_trade_bot/
├── bot.py                 # Main entry point
├── grid_trader.py         # Grid trading strategy implementation
├── binance_client.py      # Binance API client
├── logger.py              # Logging functionality
├── config.json            # Trading configuration
├── .env                   # API credentials (not in git)
├── .env.example           # Example environment file
├── requirements.txt       # Python dependencies
├── logs/                  # Log files directory
└── README.md              # This file
```

## Risk Warning

⚠️ **IMPORTANT RISK DISCLOSURE** ⚠️

- Cryptocurrency trading involves substantial risk of loss
- Grid trading can accumulate losses in strong trending markets
- Leverage amplifies both gains and losses
- This bot is for educational purposes
- Always test with small amounts first
- Never invest more than you can afford to lose
- Past performance does not guarantee future results

**USE AT YOUR OWN RISK. The developers are not responsible for any financial losses.**

## Troubleshooting

### API Connection Errors
- Verify API keys are correct in `.env`
- Check that Binance Futures API is enabled for your account
- Ensure your IP is whitelisted (if IP restriction is enabled)

### Insufficient Balance
- Ensure you have enough USDT in Binance Futures wallet
- Required balance = position_size × price / leverage

### Order Execution Failures
- Check Binance API rate limits
- Verify trading pair is available
- Ensure position size meets minimum order requirements

## Advanced Configuration

### Custom Alert Notifications (Optional)

You can add Telegram notifications by:
1. Creating a Telegram bot
2. Adding bot token and chat ID to `.env`
3. Implementing telegram alert functionality (currently not implemented)

### Adjusting Trading Parameters

To optimize for different market conditions:
- **Volatile markets**: Wider grid range, tighter stop-loss
- **Range-bound markets**: Narrower grid range, larger position size
- **Trending markets**: Consider disabling the bot or using trailing stops

## Support

For issues, questions, or contributions, please open an issue on the repository.

## License

MIT License - feel free to modify and use as needed.

---

**Disclaimer**: This software is provided "as is" without warranty of any kind. Trading cryptocurrencies carries a high level of risk and may not be suitable for all investors.
