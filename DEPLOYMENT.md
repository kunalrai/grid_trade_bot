# Deploying Grid Trading Bot to Render

This guide will help you deploy your Grid Trading Bot to Render.com.

## Prerequisites

1. A [Render](https://render.com) account (free tier available)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. CoinDCX API credentials

## Deployment Steps

### 1. Prepare Your Repository

Make sure all the deployment files are committed:
- `render.yaml` - Render deployment configuration
- `build.sh` - Build script
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create a New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your Git repository
4. Select your repository from the list

### 3. Configure the Service

Render will automatically detect the `render.yaml` file. If not, configure manually:

**Basic Settings:**
- **Name:** `grid-trading-bot` (or your preferred name)
- **Runtime:** Python 3
- **Build Command:** `./build.sh`
- **Start Command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT backend.api_server:app`

**Environment Variables:**
Set these in the Render dashboard under "Environment":

| Variable | Value | Notes |
|----------|-------|-------|
| `COINDCX_API_KEY` | Your API key | Get from CoinDCX |
| `COINDCX_API_SECRET` | Your API secret | Get from CoinDCX |
| `FLASK_SECRET_KEY` | Random string | Can auto-generate |
| `FLASK_ENV` | `production` | Optional |
| `PORT` | `10000` | Auto-set by Render |

### 4. Deploy

1. Click **"Create Web Service"**
2. Render will build and deploy your application
3. Monitor the build logs for any errors
4. Once deployed, you'll get a URL like: `https://grid-trading-bot.onrender.com`

### 5. Access Your Application

- **Frontend:** `https://your-app.onrender.com/`
- **API Health Check:** `https://your-app.onrender.com/api/health`
- **API Test:** `https://your-app.onrender.com/api/test/connection`

## Important Notes

### Free Tier Limitations

- The free tier spins down after 15 minutes of inactivity
- It takes 30-60 seconds to spin back up on first request
- Not suitable for 24/7 trading - consider paid plans for production

### Security

1. **Never commit your `.env` file** - it's in `.gitignore`
2. Set all sensitive credentials in Render's environment variables
3. Use strong API keys and secrets
4. Enable 2FA on your CoinDCX account

### File Persistence

- Render's free tier uses ephemeral storage
- Log files and trade history may be lost on restart
- Consider using a database service for persistent storage

### Updating Configuration

To update `config.json` values:
1. Use the API endpoint: `PUT /api/config`
2. Or update the file in your repo and redeploy

### Monitoring

Check your bot status:
```bash
curl https://your-app.onrender.com/api/bot/status
```

View logs in the Render dashboard under "Logs" tab.

## Troubleshooting

### Build Fails

- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure `build.sh` has execute permissions

### Application Won't Start

- Check that environment variables are set correctly
- Review application logs in Render dashboard
- Test API connection: `/api/test/connection`

### WebSocket Issues

- Ensure your frontend connects to the correct WebSocket URL
- Update frontend code to use the production URL
- Check CORS settings in `api_server.py`

### Bot Not Trading

- Verify API credentials are correct
- Check `config.json` settings
- Review logs for error messages
- Test connection endpoint first

## Upgrading to Paid Plan

For 24/7 trading:
1. Go to your service settings in Render
2. Select a paid plan (Starter or higher)
3. Your service will stay always-on

## Alternative: Manual Deployment

If you prefer not to use `render.yaml`:

1. Create Web Service manually
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT backend.api_server:app`
4. Add environment variables
5. Deploy

## Support

- [Render Documentation](https://render.com/docs)
- [CoinDCX API Docs](https://docs.coindcx.com/)

---

**Warning:** Cryptocurrency trading involves risk. Start with small amounts and test thoroughly before live trading.
