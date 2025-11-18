# Standalone Telegram Bot

This bot can run **independently** of the trading bot to monitor and control it via API.

## Features

### Works WITHOUT Authentication (Public APIs)
- `/price` - Get current market price
- `/instruments` - List all active USDT instruments
- `/health` - Check API health status

### Works WITH Authentication (Requires Trading Bot Running)
- `/status` - Get bot status
- `/pnl` - View profit & loss
- `/stats` - Trading statistics
- `/startbot` - Start the trading bot
- `/stopbot` - Stop the trading bot

## Setup

### 1. Configure Environment Variables

Add to your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_chat_id

# API Base URL (optional, defaults to http://localhost:8000)
API_BASE_URL=http://localhost:8000
```

### 2. Get Telegram Credentials

1. **Create a Telegram Bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot`
   - Follow instructions to get your `TELEGRAM_BOT_TOKEN`

2. **Get Your Chat ID:**
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Copy your Chat ID

### 3. Run the Standalone Bot

```bash
# Make sure the API server is running first
cd backend
python api_server.py

# In another terminal, run the standalone Telegram bot
python telegram_bot_standalone.py
```

## Architecture

```
┌─────────────────┐
│  Telegram App   │
│   (Your Phone)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Standalone Bot  │  ← telegram_bot_standalone.py
│  (Python)       │
└────────┬────────┘
         │ HTTP Requests
         ↓
┌─────────────────┐
│  API Server     │  ← backend/api_server.py
│   (Flask)       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Trading Bot    │  ← grid_trader_coindcx.py
│   (Optional)    │
└─────────────────┘
```

## Benefits of Standalone Mode

1. **No Trading Bot Required** for public commands
   - Check prices anytime
   - View available instruments
   - Monitor API health

2. **Separate Process** - Bot crashes won't affect Telegram
3. **Easy Restart** - Restart Telegram bot without restarting trading
4. **Remote Control** - Connect to API on any server (change `API_BASE_URL`)

## Example Usage

### Without Trading Bot Running

```
You: /price
Bot: 💰 MARKET PRICE
     Market: B-SOL_USDT
     Price: $235.4567

You: /instruments
Bot: 📊 CoinDCX Active USDT Instruments
     Total: 45 instruments
     1. B-SOL_USDT
     2. B-BTC_USDT
     ...
```

### With Trading Bot Running

```
You: /status
Bot: 🟢 Running
     State: RUNNING
     Total Trades: 15
     P&L: $123.45
     Win Rate: 73.3%

You: /stopbot
Bot: 🛑 Stopping trading bot...
     ✅ Trading bot stopped successfully!
```

## Troubleshooting

### "API is down" error
- Make sure `backend/api_server.py` is running
- Check `API_BASE_URL` in `.env` is correct
- Verify port 8000 is accessible

### "Bot not initialized" error
- This is normal for authenticated endpoints
- Start the trading bot first: `/startbot`
- Or use public endpoints like `/price`

### Commands not responding
- Check TELEGRAM_BOT_TOKEN is correct
- Ensure bot is running: `python telegram_bot_standalone.py`
- Check terminal for error messages

## Running Both Bots

You can run BOTH the integrated bot (in grid_trader) AND the standalone bot simultaneously:

1. **Integrated Bot** - Started when trading bot runs
2. **Standalone Bot** - Run separately for backup/monitoring

Both will receive the same commands and send responses independently.
