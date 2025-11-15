# SOL/USDT Grid Trading Bot - CoinDCX Edition

An automated grid trading bot for SOL/USDT perpetual futures with a modern web UI. Supports both **CoinDCX** (India's leading crypto exchange) and **Binance** platforms.

## 🚀 Features

### Trading Features
- ✅ Single-grid range trading strategy
- ✅ Automated buy/sell execution based on price levels
- ✅ Real-time price monitoring
- ✅ Position management with leverage support
- ✅ Safety rules and stop-loss protection
- ✅ Support for both CoinDCX and Binance

### Web UI Features
- 🎨 Modern, responsive web interface
- 📊 Real-time price charts
- 💰 Live P&L tracking
- 🎮 Bot control (Start/Stop/Pause/Resume)
- ⚙️ Live configuration updates
- 📈 Trade history and statistics
- 🔔 Activity log with real-time updates
- 🔌 WebSocket for instant updates

## 📋 Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [CoinDCX Setup](#coindcx-setup)
4. [Binance Setup](#binance-setup)
5. [Web UI Usage](#web-ui-usage)
6. [Configuration](#configuration)
7. [API Documentation](#api-documentation)
8. [Project Structure](#project-structure)

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- CoinDCX or Binance account with API access
- Sufficient USDT balance in Futures wallet

### Step 1: Clone and Install

```bash
git clone <repository-url>
cd grid_trade_bot

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Step 3: Set API Credentials

For **CoinDCX**:
```env
COINDCX_API_KEY=your_coindcx_api_key
COINDCX_API_SECRET=your_coindcx_api_secret
```

For **Binance**:
```env
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
```

## 🚀 Quick Start

### Option 1: Web UI (Recommended)

1. **Start the API server:**
```bash
cd backend
python api_server.py
```

2. **Open the web interface:**
```bash
# Open frontend/index.html in your browser
# Or serve it with a simple HTTP server:
cd frontend
python -m http.server 8080
```

3. **Access the UI:**
   - Open browser: `http://localhost:8080`
   - API Server: `http://localhost:5000`

### Option 2: Command Line

**For CoinDCX:**
```bash
python bot_coindcx.py
```

**For Binance:**
```bash
python bot.py
```

## 🇮🇳 CoinDCX Setup

### Get API Keys

1. Go to [CoinDCX API Dashboard](https://coindcx.com/api-dashboard)
2. Create a new API key
3. Enable Futures Trading permission
4. Save API Key and Secret

### Configure for CoinDCX

Edit `config.json`:
```json
{
  "trading": {
    "market": "SOLUSDT",
    "symbol": "SOL/USDT",
    "buy_level": 138.00,
    "sell_level": 143.00,
    "position_size": 10,
    "leverage": 1,
    "order_type": "limit"
  }
}
```

### Transfer Funds to Futures Wallet

CoinDCX separates Spot and Futures wallets. Transfer USDT to Futures:

```python
# The bot can do this programmatically
client.transfer_to_futures('USDT', 1000)
```

Or manually via CoinDCX web interface.

### Run CoinDCX Bot

**Command Line:**
```bash
python bot_coindcx.py
```

**Web UI:**
- Start backend: `python backend/api_server.py`
- Open `frontend/index.html`
- Click "Start Bot"

## 🌐 Binance Setup

### Get API Keys

1. Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key
3. Enable Futures Trading
4. (Optional) Whitelist your IP

### Test with Binance Testnet

Use testnet for risk-free testing:

1. Get testnet keys: [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Edit `bot.py` and set `testnet=True`:
```python
client = BinanceFuturesClient(
    api_key=api_key,
    api_secret=api_secret,
    testnet=True,  # Enable testnet
    logger=logger
)
```

## 🎨 Web UI Usage

### Dashboard Overview

The web interface provides real-time monitoring and control:

#### 1. **Bot Control Panel**
- Start/Stop/Pause/Resume bot
- View current bot status
- See connection status

#### 2. **Price Monitor**
- Current SOL/USDT price
- Buy/Sell levels
- Live price chart

#### 3. **Trading Statistics**
- Total trades executed
- Win rate percentage
- Cumulative P&L
- Cycles completed

#### 4. **Current Position**
- Active position details
- Entry price
- Unrealized P&L

#### 5. **Configuration**
- Adjust trading parameters
- Set position size and leverage
- Update buy/sell levels
- Save changes in real-time

#### 6. **Recent Trades**
- Last 10 trades
- Profit/loss per trade
- Timestamp

#### 7. **Activity Log**
- Real-time bot actions
- Error messages
- Status updates

### UI Screenshots

```
┌─────────────────────────────────────────────────┐
│  🤖 SOL/USDT Grid Trading Bot                   │
│     CoinDCX Futures Trading              ● Connected
└─────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────┐
│ 🎮 Bot Control   │  📍 Current Position          │
│ ● Running        │  LONG 10 SOL @ $138.50       │
│ ▶ Start  ⏹ Stop │  Unrealized P&L: +$25.00     │
│ ⏸ Pause  ▶ Resume│                               │
├──────────────────┤──────────────────────────────┤
│ 💰 Price Monitor │  ⚙️ Configuration            │
│ $141.25          │  Position Size: 10 SOL       │
│ Sell: $143.00    │  Leverage: 1x                │
│ Buy:  $138.00    │  Buy: $138.00                │
│ [Price Chart]    │  Sell: $143.00               │
├──────────────────┤──────────────────────────────┤
│ 📊 Statistics    │  📈 Recent Trades            │
│ Trades: 12       │  SELL 10 SOL @ $143.00 +$50  │
│ Win Rate: 100%   │  BUY  10 SOL @ $138.00       │
│ Total P&L: +$300 │  SELL 10 SOL @ $143.00 +$50  │
└──────────────────┴──────────────────────────────┘
```

## ⚙️ Configuration

### Trading Parameters

```json
{
  "trading": {
    "market": "SOLUSDT",        // Trading pair
    "buy_level": 138.00,        // Buy trigger price
    "sell_level": 143.00,       // Sell trigger price
    "position_size": 10,        // SOL per trade
    "leverage": 1,              // 1x to 10x
    "order_type": "limit"       // "limit" or "market"
  }
}
```

### Safety Settings

```json
{
  "safety": {
    "max_cumulative_loss": -50.0,  // Stop if loss exceeds
    "support_level": 135.0,        // Alert below this
    "resistance_level": 146.0,     // Alert above this
    "trading_range_min": 135.0,    // Pause below this
    "trading_range_max": 146.0     // Pause above this
  }
}
```

### Monitoring Settings

```json
{
  "monitoring": {
    "check_interval_seconds": 60,  // Price check frequency
    "enable_console_output": true
  }
}
```

## 📡 API Documentation

### REST Endpoints

#### Bot Control

**Start Bot**
```http
POST /api/bot/start
Response: { "success": true, "status": {...} }
```

**Stop Bot**
```http
POST /api/bot/stop
Response: { "success": true }
```

**Pause Bot**
```http
POST /api/bot/pause
Response: { "success": true }
```

**Resume Bot**
```http
POST /api/bot/resume
Response: { "success": true }
```

**Get Status**
```http
GET /api/bot/status
Response: {
  "state": "running",
  "current_price": 141.25,
  "total_trades": 12,
  "cumulative_pnl": 300.00,
  ...
}
```

#### Market Data

**Get Price**
```http
GET /api/market/price?market=SOLUSDT
Response: { "price": 141.25 }
```

**Get Balance**
```http
GET /api/account/balance
Response: { "USDT": 5000.00 }
```

#### Configuration

**Get Config**
```http
GET /api/config
Response: { "trading": {...}, "safety": {...} }
```

**Update Config**
```http
PUT /api/config
Body: { "trading": { "position_size": 15 } }
Response: { "success": true }
```

### WebSocket Events

**Connect**
```javascript
socket = io('http://localhost:5000');
```

**Status Updates**
```javascript
socket.on('status_update', (status) => {
  console.log(status);
});
```

**Request Status**
```javascript
socket.emit('request_status');
```

## 📁 Project Structure

```
grid_trade_bot/
├── backend/
│   └── api_server.py           # Flask API server
├── frontend/
│   ├── index.html              # Web UI
│   ├── styles.css              # Styling
│   └── app.js                  # Frontend logic
├── bot.py                      # Binance bot entry point
├── bot_coindcx.py              # CoinDCX bot entry point
├── binance_client.py           # Binance API client
├── coindcx_client.py           # CoinDCX API client
├── grid_trader.py              # Binance grid trader
├── grid_trader_coindcx.py      # CoinDCX grid trader
├── logger.py                   # Logging system
├── config.json                 # Configuration
├── requirements.txt            # Dependencies
├── .env                        # API credentials
└── README_COINDCX.md           # This file
```

## 🔒 Security Best Practices

1. **API Key Permissions**
   - Only enable required permissions (Futures Trading)
   - Never share your API secret
   - Use IP whitelist if available

2. **Environment Variables**
   - Never commit `.env` to git
   - Use strong secret keys
   - Rotate API keys regularly

3. **Testing**
   - Always test with small amounts first
   - Use testnet when available
   - Verify configuration before live trading

## 🐛 Troubleshooting

### Connection Issues

**CoinDCX API 403 Error:**
- Check API key permissions
- Verify Futures trading is enabled
- Check timestamp synchronization

**WebSocket Disconnects:**
- Check firewall settings
- Verify server is running
- Check network connectivity

### Trading Issues

**Orders Not Executing:**
- Verify sufficient balance
- Check minimum order size
- Verify price is within limits

**Position Not Detected:**
- Check market symbol format
- Verify position exists on exchange
- Check API permissions

## ⚠️ Risk Disclaimer

**IMPORTANT: READ CAREFULLY**

- Cryptocurrency trading involves substantial risk of loss
- Grid trading can accumulate losses in trending markets
- This bot is for educational purposes
- Always test with small amounts first
- Never invest more than you can afford to lose
- Past performance does not guarantee future results

**USE AT YOUR OWN RISK**

The developers are not responsible for any financial losses incurred while using this software.

## 📝 License

MIT License - Free to use and modify

## 🤝 Support

For issues or questions:
- Check troubleshooting section
- Review configuration
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Multiple grid levels support
- [ ] Stop-loss and take-profit orders
- [ ] Telegram notifications
- [ ] Email alerts
- [ ] Historical performance analytics
- [ ] Backtesting module
- [ ] Mobile-responsive UI improvements

---

**Happy Trading! 🚀**
