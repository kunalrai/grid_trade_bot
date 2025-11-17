# Keep-Alive Configuration for Render

This document explains how the keep-alive feature prevents Render from timing out the application after 15 minutes of inactivity.

## Problem

Render's free tier services spin down after 15 minutes of inactivity. This can interrupt:
- Active trading operations
- WebSocket connections
- Real-time monitoring

## Solution

We've implemented a multi-layered keep-alive system:

### 1. Backend Health Check Endpoints

**Location:** `backend/api_server.py`

Two endpoints are available:

#### `/api/health` (Enhanced Health Check)
```python
GET /api/health

Response:
{
  "status": "ok",
  "timestamp": "2025-11-17T10:30:00.000Z",
  "uptime": "2025-11-17T10:30:00.000Z",
  "bot_running": true,
  "bot_state": "running"
}
```

This endpoint provides:
- Server health status
- Current timestamp
- Bot running state
- Bot current state

#### `/api/ping` (Lightweight Ping)
```python
GET/POST /api/ping

Response:
{
  "pong": true,
  "timestamp": "2025-11-17T10:30:00.000Z"
}
```

This is a minimal endpoint designed for frequent keep-alive requests.

### 2. Frontend Periodic Ping

**Location:** `frontend/app.js` (lines 809-830)

The frontend automatically pings the server every **10 minutes**:

```javascript
// Keep-alive ping every 10 minutes
setInterval(() => {
    fetch(`${API_BASE_URL}/api/ping`)
        .then(response => response.json())
        .then(data => {
            console.log('Keep-alive ping successful:', data.timestamp);
        })
        .catch(error => {
            console.warn('Keep-alive ping failed:', error);
        });
}, 10 * 60 * 1000); // 10 minutes
```

**Benefits:**
- Runs automatically when the frontend is open
- Keeps the server active
- Logs success/failure in browser console
- No user interaction required

### 3. Render Configuration

**Location:** `render.yaml` (line 20)

```yaml
healthCheckPath: /api/health
```

Render periodically checks this endpoint to verify service health.

## Usage Scenarios

### Scenario 1: Active Trading
When the web interface is open in your browser:
- ✅ Automatic keep-alive pings every 10 minutes
- ✅ WebSocket status updates every 1 second
- ✅ No timeout issues

### Scenario 2: Headless Operation (No Browser Open)

For 24/7 operation without keeping a browser tab open, use **external monitoring services**:

#### Option A: UptimeRobot (Recommended - Free)
1. Sign up at [uptimerobot.com](https://uptimerobot.com/)
2. Create a new monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://your-app.onrender.com/api/ping`
   - **Interval:** 10 minutes
   - **Alert contacts:** Your email

#### Option B: Pingdom
1. Sign up at [pingdom.com](https://www.pingdom.com/)
2. Create uptime check for `/api/health`
3. Set interval to 10 minutes

#### Option C: Custom Cron Job
Using GitHub Actions or any server with cron:

```bash
# Every 10 minutes
*/10 * * * * curl https://your-app.onrender.com/api/ping
```

#### Option D: Simple Script
```python
# keep_alive_client.py
import requests
import time

APP_URL = "https://your-app.onrender.com"

while True:
    try:
        response = requests.get(f"{APP_URL}/api/ping")
        print(f"Ping successful: {response.json()}")
    except Exception as e:
        print(f"Ping failed: {e}")

    time.sleep(600)  # 10 minutes
```

### Scenario 3: Telegram Bot Integration

If you're using the Telegram bot feature, consider adding a `/keepalive` command:

```python
# In telegram_notifier.py or bot command handler
@bot.message_handler(commands=['keepalive'])
def cmd_keepalive(message):
    # This command execution itself keeps the server alive
    bot.reply_to(message, "✅ Server is alive and running!")
```

## Monitoring

### Check Keep-Alive Status

**Browser Console:**
When the frontend is open, check the browser console for:
```
Keep-alive ping successful: 2025-11-17T10:30:00.000Z
```

**Manual Test:**
```bash
curl https://your-app.onrender.com/api/ping
```

**Expected Response:**
```json
{
  "pong": true,
  "timestamp": "2025-11-17T10:30:00.000Z"
}
```

### Troubleshooting

**Problem:** Server still spinning down
- ✅ Verify external monitor is hitting the correct URL
- ✅ Check monitor interval is < 15 minutes
- ✅ Ensure Render service is set to "web" type
- ✅ Check Render logs for errors

**Problem:** Frontend pings not working
- ✅ Open browser console (F12)
- ✅ Look for keep-alive log messages
- ✅ Check for CORS errors
- ✅ Verify API_BASE_URL is correct

## Best Practices

1. **Use Multiple Methods:**
   - Frontend ping (when browser open)
   - External monitor (for 24/7 operation)

2. **Set Appropriate Intervals:**
   - Keep-alive: 10 minutes
   - Status updates: 1 second
   - Wallet refresh: 30 seconds

3. **Monitor Server Logs:**
   - Check Render dashboard for spin-up/spin-down events
   - Monitor ping success rate
   - Track bot uptime

4. **Upgrade to Paid Plan (Optional):**
   - Render paid plans ($7/month) don't spin down
   - Better for production trading
   - No keep-alive needed

## Configuration Summary

| Component | Interval | Purpose |
|-----------|----------|---------|
| Frontend ping | 10 min | Keep server alive when browser open |
| Status update | 1 sec | Real-time bot monitoring |
| Wallet refresh | 30 sec | Balance updates |
| External monitor | 10 min | 24/7 keep-alive (optional) |
| Render health check | Varies | Automatic service verification |

## Security Considerations

- `/api/ping` is publicly accessible (read-only)
- `/api/health` is publicly accessible (read-only)
- No sensitive data exposed in these endpoints
- No authentication required for keep-alive
- Trading operations still require valid API keys

## Cost

- **Render Free Tier:** $0/month (with keep-alive)
- **UptimeRobot:** $0/month (50 monitors free)
- **Pingdom:** Free trial, then paid
- **GitHub Actions:** Free (2000 minutes/month)

## Next Steps

1. ✅ Keep-alive feature is already implemented
2. ⏭️ Set up external monitor (UptimeRobot recommended)
3. ⏭️ Monitor browser console for ping confirmations
4. ⏭️ Consider upgrading to paid Render plan for production use

---

**Note:** Keep-alive is most critical when running the bot 24/7 without browser access. If you're actively monitoring via the web interface, the frontend pings will handle it automatically.
