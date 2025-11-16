# Auto-Start Feature

The Grid Trading Bot now supports automatic startup when you run the API server!

## How It Works

When you run:
```bash
python backend/api_server.py
```

The bot will automatically:
1. ✅ Load your configuration from `config.json`
2. ✅ Connect to CoinDCX API
3. ✅ Start the Telegram bot (if configured)
4. ✅ Begin monitoring and trading automatically

**No need to manually start the bot from the UI!**

## Configuration

Auto-start is controlled by the `auto_start_bot` setting in `config.json`:

```json
{
  "monitoring": {
    "auto_start_bot": true
  }
}
```

- `true` - Bot starts automatically when API server runs
- `false` - Bot waits for manual start from UI or Telegram

## Controlling the Bot via Telegram

You can now fully control your bot from Telegram:

### Start the Bot
```
/startbot
```

### Stop the Bot
```
/stopbot
```

### Restart the Bot
```
/restart
```

### Check Status
```
/status
```

## Usage Examples

### Example 1: Run and Forget
```bash
# Start the server - bot auto-starts
python backend/api_server.py

# Bot is now running and trading
# Control it from Telegram using /stopbot or /restart
```

### Example 2: Manual Control
Edit `config.json`:
```json
{
  "monitoring": {
    "auto_start_bot": false
  }
}
```

Then:
```bash
# Start the server
python backend/api_server.py

# Bot is NOT running yet
# Start it from Telegram: /startbot
```

## Deployment

### Local Development
```bash
# Set environment variables
export COINDCX_API_KEY="your_key"
export COINDCX_API_SECRET="your_secret"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run
python backend/api_server.py
```

### Fly.io Deployment
```bash
# Set secrets
fly secrets set COINDCX_API_KEY="your_key"
fly secrets set COINDCX_API_SECRET="your_secret"
fly secrets set TELEGRAM_BOT_TOKEN="your_token"
fly secrets set TELEGRAM_CHAT_ID="your_chat_id"

# Deploy
fly deploy
```

The bot will auto-start on deployment!

## Benefits

✅ **Convenience** - No need to click "Start" in UI
✅ **Cloud-Ready** - Perfect for deployment on Fly.io/Render
✅ **Telegram Control** - Full control from your phone
✅ **Always Running** - Restarts automatically on server restart
✅ **Fail-Safe** - If auto-start fails, you can still start from Telegram

## Troubleshooting

### Bot doesn't auto-start?

1. **Check config.json:**
   ```json
   "auto_start_bot": true
   ```

2. **Check environment variables:**
   ```bash
   echo $COINDCX_API_KEY
   echo $COINDCX_API_SECRET
   ```

3. **Check logs:**
   Look for messages like:
   ```
   🚀 Auto-starting trading bot...
   ✅ Trading bot auto-started successfully!
   ```

4. **Manual start from Telegram:**
   ```
   /startbot
   ```

## Workflow

### Typical Daily Workflow

1. **Morning:** Bot is already running (auto-started)
2. **Check status:** `/status` in Telegram
3. **View P&L:** `/pnl` in Telegram
4. **Need to stop?** `/stopbot` in Telegram
5. **Restart after config change:** `/restart` in Telegram

### When You Make Config Changes

If you edit `config.json`:
```
/restart
```

The bot will reload the new configuration!

---

**You're now ready for hands-free trading!** 🚀
