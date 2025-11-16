# Telegram Bot Setup Guide

This guide will help you set up Telegram notifications for your Grid Trading Bot.

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather
3. **Send** `/newbot` command
4. **Choose a name** for your bot (e.g., "My Grid Trading Bot")
5. **Choose a username** for your bot (must end with 'bot', e.g., "my_grid_trading_bot")
6. **Copy the API token** - BotFather will give you a token that looks like:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

## Step 2: Get Your Chat ID

### Method 1: Using a Bot (Easiest)

1. **Search** for `@userinfobot` in Telegram
2. **Start** the bot
3. **Copy your ID** - it will show something like: `Your ID: 123456789`

### Method 2: Manual Method

1. **Send a message** to your newly created bot (from Step 1)
2. **Open your browser** and go to:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual token from Step 1
3. **Find your chat ID** in the JSON response - look for `"chat":{"id":123456789}`

## Step 3: Configure Environment Variables

### Option A: Using .env file (Recommended for local development)

1. **Create or edit** `.env` file in your project root:
   ```bash
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

2. **Replace** with your actual values from Steps 1 and 2

### Option B: Set environment variables directly

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
$env:TELEGRAM_CHAT_ID="123456789"
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"
```

### Option C: Fly.io deployment

```bash
fly secrets set TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
fly secrets set TELEGRAM_CHAT_ID="123456789"
```

## Step 4: Enable Telegram Alerts

The Telegram alerts are already enabled in `config.json`:

```json
{
  "monitoring": {
    "enable_telegram_alerts": true
  }
}
```

If you want to disable Telegram alerts temporarily, set it to `false`.

## Step 5: Test Your Bot

1. **Start your trading bot** as usual
2. **Check Telegram** - you should receive a startup message:
   ```
   🤖 Grid Trading Bot Started!

   Use /help to see available commands.
   ```

3. **Try commands** in Telegram:
   - `/start` - Welcome message
   - `/status` - Get bot status
   - `/pnl` - View profit & loss
   - `/position` - Check current position
   - `/stats` - Trading statistics
   - `/help` - Show all commands

## Available Telegram Commands

### 🎮 Bot Control Commands

| Command | Description |
|---------|-------------|
| `/startbot` | Start the trading bot |
| `/stopbot` | Stop the trading bot |
| `/restart` | Restart the trading bot |

### 📊 Information Commands

| Command | Description |
|---------|-------------|
| `/status` | Get current bot status and configuration |
| `/pnl` | View total profit & loss |
| `/position` | Check current open position |
| `/stats` | View trading statistics |
| `/help` | Show all available commands |

### ℹ️ Other Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |

## Notifications You'll Receive

### 🟢 Buy Order Executed
```
🟢 BUY ORDER EXECUTED

Market: B-SOL_USDT
Quantity: 10.0
Price: $139.5000
Time: 2025-11-16 18:45:23
```

### 🔴 Sell Order Executed
```
🔴 SELL ORDER EXECUTED

Market: B-SOL_USDT
Quantity: 10.0
Price: $143.2000
Time: 2025-11-16 19:15:42
```

### ⚠️ Errors
```
⚠️ ERROR

Connection to exchange failed
Time: 2025-11-16 18:45:23
```

### 🛑 Bot Stopped
```
🛑 BOT STOPPED

Reason: User requested stop
Time: 2025-11-16 20:00:00
```

## Troubleshooting

### Not receiving messages?

1. **Check** that you've sent at least one message to your bot first
2. **Verify** your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are correct
3. **Ensure** `enable_telegram_alerts` is set to `true` in `config.json`
4. **Check logs** for any Telegram-related errors

### Bot commands not working?

1. **Make sure** the bot is running
2. **Try** `/start` command first
3. **Check** that you're messaging the correct bot

### "Telegram credentials not found" error

- **Verify** environment variables are set correctly
- **Check** `.env` file exists and has the correct format
- **Restart** the bot after setting environment variables

## Privacy & Security

- **Keep your bot token secret** - treat it like a password
- **Never commit** your `.env` file to git (it's already in `.gitignore`)
- **Only you** (the chat ID owner) can use the bot commands
- **Telegram messages** are encrypted end-to-end

## Advanced: Multiple Users

To allow multiple users to receive notifications:

1. Each user gets their chat ID using `@userinfobot`
2. You'll need to modify `telegram_notifier.py` to support multiple chat IDs
3. Or create separate bots for each user

---

## Need Help?

If you encounter issues:
1. Check the bot logs for error messages
2. Verify all environment variables are set correctly
3. Test your bot token using Telegram's API:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

Happy Trading! 📈
