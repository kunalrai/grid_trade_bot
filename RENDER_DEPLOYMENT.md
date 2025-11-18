# Deploying Standalone Telegram Bot on Render

This guide will help you deploy the standalone Telegram bot as a background worker on Render.

---

## 🚀 Deployment Methods

### **Method 1: Deploy Using render.yaml (Recommended)**

This method automatically creates both services (API + Telegram bot) from your repository.

#### Step 1: Prepare Your Repository

Ensure these files exist in your repo:
- ✅ [telegram_bot_standalone.py](telegram_bot_standalone.py)
- ✅ [technical_analysis.py](technical_analysis.py)
- ✅ [requirements.txt](requirements.txt)
- ✅ [render.yaml](render.yaml)

#### Step 2: Push to GitHub

```bash
git add .
git commit -m "Add standalone Telegram bot for Render deployment"
git push origin main
```

#### Step 3: Connect to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect [render.yaml](render.yaml)
5. Click **"Apply"**

#### Step 4: Configure Environment Variables

Render will create TWO services:
1. **grid-trading-bot** (Web Service) - Flask API
2. **telegram-bot-standalone** (Background Worker) - Telegram Bot

For the **telegram-bot-standalone** service, set these environment variables:

| Variable | Value | Where to Get It |
|----------|-------|-----------------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Your chat ID | Message `@userinfobot` on Telegram |
| `API_BASE_URL` | `https://grid-trading-bot.onrender.com` | Your web service URL from Render |

**Important:** Update `API_BASE_URL` in [render.yaml](render.yaml) line 38 with your actual Render web service URL.

#### Step 5: Deploy

- Render will automatically build and deploy both services
- Monitor logs in the Render dashboard
- Look for: `✅ Telegram bot started and listening for commands`

---

### **Method 2: Deploy Bot Only (Manual)**

If you only want to deploy the Telegram bot without the API server:

#### Step 1: Create New Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Background Worker"**
3. Connect your GitHub repository

#### Step 2: Configure Service

- **Name:** `telegram-bot-standalone`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python telegram_bot_standalone.py`

#### Step 3: Set Environment Variables

Add these in the Render dashboard:

```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
API_BASE_URL=http://localhost:8000
PYTHON_VERSION=3.11.0
```

**Note:** If you're NOT deploying the API server, set `API_BASE_URL=http://localhost:8000`. The bot will still work for technical analysis commands (`/scan`, `/signals`, `/analyze`).

#### Step 4: Deploy

- Click **"Create Background Worker"**
- Wait for deployment to complete
- Check logs for `✅ Telegram bot started and listening for commands`

---

## 🔧 Environment Variables Explained

### **TELEGRAM_BOT_TOKEN** (Required)

Get this from [@BotFather](https://t.me/BotFather) on Telegram:

1. Send `/start` to BotFather
2. Send `/newbot` (or use existing bot)
3. Follow prompts to get your token
4. Token format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### **TELEGRAM_CHAT_ID** (Required)

Get your chat ID:

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID (e.g., `123456789`)
3. Use this as your `TELEGRAM_CHAT_ID`

### **API_BASE_URL** (Optional)

- **If deploying API server:** Set to your Render web service URL (e.g., `https://grid-trading-bot.onrender.com`)
- **If NOT deploying API server:** Leave as `http://localhost:8000`

**What works without API server:**
- ✅ `/analyze` - Technical analysis (uses CoinDCX public API)
- ✅ `/scan` - Market scanning (uses CoinDCX public API)
- ✅ `/signals` - Trading signals (uses CoinDCX public API)

**What requires API server:**
- ❌ `/startbot`, `/stopbot` - Bot control
- ❌ `/status` - Trading bot status
- ❌ `/pnl` - Profit & loss
- ❌ `/stats` - Trading statistics

---

## ✅ Verify Deployment

### 1. Check Logs

In Render dashboard, go to your service and check logs:

```
Telegram bot started and listening for commands
INFO - Application started successfully
```

### 2. Test on Telegram

Send these commands to your bot:

```
/start          # Should get welcome message
/help           # Should show all commands
/scan 5m 4h     # Should scan 15 coins on 2 timeframes
/analyze BTC    # Should analyze Bitcoin
```

### 3. Check Commands Work

**Technical Analysis (No API needed):**
```
/analyze SOL 4h
/scan
/signals
```

**Bot Control (Needs API server):**
```
/status
/startbot
/health
```

---

## 🐛 Troubleshooting

### Bot Not Responding

**Check 1: Token is correct**
```bash
# Test your token (replace with yours)
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

Should return bot info. If error, token is invalid.

**Check 2: Logs show errors**

Look for these in Render logs:
- `Invalid token` → Wrong `TELEGRAM_BOT_TOKEN`
- `Connection error` → Network issue (restart service)
- `Module not found` → Build failed (check requirements.txt)

**Check 3: Environment variables set**

Render dashboard → Your Service → Environment → Check all variables are present

### Commands Return Errors

**`/analyze` fails:**
- Check CoinDCX public API is accessible
- Verify coin symbol is correct (use `/analyze BTC`, not `/analyze BTCUSDT`)

**`/startbot` fails:**
- Verify `API_BASE_URL` is set correctly
- Check web service is running
- Test health: `curl https://your-app.onrender.com/api/health`

### Free Tier Sleep Issue

Render free tier sleeps after 15 minutes of inactivity.

**Solution:**
1. The bot's polling mechanism should keep it awake
2. If it still sleeps, upgrade to paid plan ($7/month)
3. Or use an external ping service (not recommended for bots)

---

## 🔄 Updates and Redeployment

### Auto-Deploy

If you enabled auto-deploy in render.yaml:

```bash
git add .
git commit -m "Update bot"
git push origin main
```

Render will automatically redeploy.

### Manual Deploy

1. Go to Render dashboard
2. Click your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 📊 Resource Usage

**Free Tier Limits:**
- 750 hours/month (enough for 1 service running 24/7)
- Sleeps after 15 min inactivity (bot polling prevents this)
- 512 MB RAM (sufficient for this bot)

**Expected Usage:**
- CPU: ~2-5% (idle), ~10-20% (during `/scan`)
- RAM: ~50-100 MB
- Network: Minimal (only when commands are used)

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets

**❌ DON'T:**
```bash
git add .env
```

**✅ DO:**
- Add `.env` to `.gitignore`
- Set secrets in Render dashboard

### 2. Regenerate Exposed Tokens

If you accidentally commit your bot token:

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot → **API Token** → **Revoke**
4. Update `TELEGRAM_BOT_TOKEN` in Render

### 3. Restrict Bot Access

In your bot code, you can add chat ID validation:

```python
# In telegram_bot_standalone.py (already implemented)
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
```

Only the configured chat ID can use the bot.

---

## 💡 Tips for Production

### 1. Use Webhook Mode (Better for Render)

Current implementation uses **polling** (bot constantly checks for updates). For production, consider webhook mode:

```python
# Future enhancement - webhook mode
await application.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get('PORT', 8080)),
    webhook_url=f"{os.environ['RENDER_EXTERNAL_URL']}/{SECRET_TOKEN}",
)
```

I can help implement this if needed.

### 2. Add Health Check

Current bot doesn't expose an HTTP endpoint. For better monitoring:

```python
# Future enhancement - add HTTP health endpoint
from flask import Flask
health_app = Flask(__name__)

@health_app.route('/health')
def health():
    return {'status': 'ok', 'bot': 'running'}
```

### 3. Enable Logging

Logs are already configured. View them in Render dashboard.

---

## 📈 Scaling

### Current Setup (Free Tier)
- 1 background worker
- Handles commands sequentially
- Good for personal use (1-10 users)

### For Higher Usage
- Upgrade to paid plan ($7/month)
- More RAM and CPU
- Better uptime guarantees
- No sleep after inactivity

---

## 🆘 Support

### Check Logs First

Render Dashboard → Your Service → Logs

Look for:
- `✅` Success messages
- `❌` Error messages
- Stack traces

### Common Error Solutions

| Error | Solution |
|-------|----------|
| `Module 'telegram' not found` | Build failed. Check requirements.txt |
| `Invalid token` | Wrong TELEGRAM_BOT_TOKEN |
| `Connection refused` | API_BASE_URL incorrect or server down |
| `Timeout` | Network issue, restart service |
| `Memory limit exceeded` | Bot scanning too many coins, reduce list |

---

## ✅ Deployment Checklist

Before deploying:

- [ ] Repository pushed to GitHub
- [ ] [render.yaml](render.yaml) updated with correct URLs
- [ ] [requirements.txt](requirements.txt) includes all dependencies
- [ ] `.env` added to `.gitignore`
- [ ] Bot token obtained from BotFather
- [ ] Chat ID obtained from userinfobot

After deploying:

- [ ] Service shows "Live" status in Render
- [ ] Logs show "Telegram bot started"
- [ ] `/start` command works on Telegram
- [ ] `/scan` returns market data
- [ ] `/analyze BTC` returns analysis

---

## 🚀 Quick Start Summary

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy standalone Telegram bot"
git push origin main

# 2. Create Render Blueprint
# Visit render.com → New Blueprint → Select your repo

# 3. Set environment variables in Render dashboard:
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
API_BASE_URL=https://your-app.onrender.com

# 4. Deploy and test
# Send /start to your bot on Telegram
```

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [CoinDCX Public API](https://docs.coindcx.com/)

---

**Need Help?**

Check the logs in Render dashboard for detailed error messages. Most issues are related to incorrect environment variables or network connectivity.

Happy Trading! 🎉
