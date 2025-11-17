# Deployment Guide for Grid Trading Bot

## Overview
This guide will help you deploy the SOL/USDT Grid Trading Bot to cloud platforms like Render, Railway, or Heroku.

## Important Changes Made

### 1. Frontend URL Auto-Detection
The frontend now automatically detects whether it's running locally or in production:
- **Local**: Uses `http://localhost:5000`
- **Production**: Uses the same origin as the web page (e.g., `https://your-app.onrender.com`)

### 2. Config File Handling
The backend now gracefully handles read-only file systems:
- Configuration changes are stored in memory
- If file system is writable, config is persisted to disk
- If not (common in cloud deployments), config remains in memory until restart

### 3. Port Configuration
The server now reads the `PORT` environment variable (required by most cloud platforms):
```python
port = int(os.getenv('PORT', 5000))
```

## Deployment on Render

### Method 1: Using render.yaml (Recommended)

1. **Create a new Web Service on Render**
   - Go to https://dashboard.render.com/
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Environment Variables**
   In the Render dashboard, add these environment variables:
   - `COINDCX_API_KEY` - Your CoinDCX API key
   - `COINDCX_API_SECRET` - Your CoinDCX API secret
   - `FLASK_SECRET_KEY` - Will be auto-generated from render.yaml

3. **Deploy**
   - Render will automatically detect `render.yaml`
   - Click "Create Web Service"
   - Wait for deployment to complete

### Method 2: Manual Configuration

1. **Create Web Service**
   - Name: `grid-trading-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python backend/api_server.py`

2. **Set Environment Variables** (same as above)

3. **Deploy**

## Deployment on Railway

1. **Create New Project**
   - Go to https://railway.app/
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Settings**
   - Railway auto-detects Python
   - Start Command: `python backend/api_server.py`

3. **Add Environment Variables**
   - `COINDCX_API_KEY`
   - `COINDCX_API_SECRET`
   - `FLASK_SECRET_KEY` (generate a random string)
   - `PORT` (Railway sets this automatically)

4. **Deploy**

## Deployment on Heroku

1. **Install Heroku CLI**
   ```bash
   # Follow instructions at https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Procfile**
   Already included in the repository with:
   ```
   web: python backend/api_server.py
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set COINDCX_API_KEY=your_key_here
   heroku config:set COINDCX_API_SECRET=your_secret_here
   heroku config:set FLASK_SECRET_KEY=random_secret_key
   ```

## Common Issues and Solutions

### Issue: "Failed to fetch" when saving config

**Cause**: The frontend was using hardcoded `localhost:5000` which doesn't work in production.

**Solution**: Already fixed! The frontend now auto-detects the correct URL.

### Issue: Config changes not persisting

**Cause**: Cloud platforms often have read-only file systems.

**Solution**:
- Config changes work in memory during the session
- For persistent storage, consider using environment variables or a database
- Alternatively, use a cloud storage service (S3, Google Cloud Storage, etc.)

### Issue: WebSocket connection fails

**Cause**: Some cloud platforms require specific WebSocket configuration.

**Solution**: Ensure your platform supports WebSockets:
- ✅ Render: Supported
- ✅ Railway: Supported
- ✅ Heroku: Supported (requires specific dyno types)

### Issue: Bot stops after 30 seconds

**Cause**: Some free tiers timeout inactive connections.

**Solution**:
- Upgrade to a paid tier
- Implement keep-alive pings
- Use a service like UptimeRobot to ping your app

## Testing Your Deployment

1. **Check Health Endpoint**
   ```bash
   curl https://your-app-url.com/api/health
   ```

2. **Access Web UI**
   - Open `https://your-app-url.com` in your browser
   - Should see the trading bot dashboard

3. **Test Configuration**
   - Try changing config values
   - Click "Save Configuration"
   - Should see "Configuration saved successfully" (or warning about in-memory storage)

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `COINDCX_API_KEY` | Yes | Your CoinDCX Futures API key |
| `COINDCX_API_SECRET` | Yes | Your CoinDCX Futures API secret |
| `FLASK_SECRET_KEY` | Recommended | Secret key for Flask sessions (auto-generated on Render) |
| `PORT` | Auto-set | Port number (set automatically by most platforms) |

## Security Recommendations

1. **Never commit API keys** to your repository
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** (automatic on Render/Railway/Heroku)
4. **Rotate your API keys** regularly
5. **Set up IP whitelisting** on CoinDCX if possible
6. **Monitor your deployment logs** for suspicious activity

## Monitoring and Logs

### Render
```bash
# View logs in dashboard or CLI
render logs -f
```

### Railway
```bash
# View logs in dashboard
```

### Heroku
```bash
heroku logs --tail
```

## Troubleshooting Checklist

- [ ] All environment variables are set correctly
- [ ] API keys are valid and have futures trading permissions
- [ ] Port is set correctly (or using environment variable)
- [ ] Frontend can reach backend API
- [ ] WebSocket connection is established
- [ ] CORS is configured properly
- [ ] Logs show no errors

## Next Steps

1. Set up monitoring and alerts
2. Configure stop-loss and take-profit levels
3. Test with small position sizes first
4. Monitor performance regularly
5. Set up backup and disaster recovery

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Test the health endpoint
4. Review the troubleshooting checklist
