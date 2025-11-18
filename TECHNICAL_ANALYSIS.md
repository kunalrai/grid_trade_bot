# Technical Analysis Features

The Telegram bot now includes powerful technical analysis capabilities for BTC, ETH, SOL, and ZEC!

## 🎯 Features

### Indicators Analyzed:
- **RSI (14)** - Relative Strength Index for overbought/oversold conditions
- **MACD** - Moving Average Convergence Divergence with histogram
- **EMA 20 & EMA 50** - Exponential Moving Averages
- **Volume Analysis** - Current vs average volume
- **Golden Cross / Death Cross Detection** - EMA crossover signals
- **Multi-Timeframe Analysis** - 5-minute and 4-hour candles

### Signal Generation:
The bot combines all indicators to generate:
- **Strong Buy** 🟢🟢
- **Buy** 🟢
- **Neutral** ⚪
- **Sell** 🔴
- **Strong Sell** 🔴🔴

## 📱 Telegram Commands

### 1. `/analyze <COIN> [TIMEFRAME]`

Get detailed technical analysis for a specific coin.

**Examples:**
```
/analyze BTC          # Bitcoin on 5m (default)
/analyze ETH 4h       # Ethereum on 4h
/analyze SOL          # Solana on 5m
/analyze ZEC 4h       # Zcash on 4h
```

**Output includes:**
- Current price, high, low
- RSI value and status (oversold/overbought)
- MACD values and trend
- EMA20, EMA50 values and trend
- Golden/Death cross alerts
- Volume analysis
- Overall signal strength

**Example Output:**
```
📊 BTC/USDT Technical Analysis (5m)
━━━━━━━━━━━━━━━━━━

💰 Price: $45,234.56
High: $45,500.00 | Low: $45,000.00

📈 RSI (14): 32.45
Status: OVERSOLD

📉 MACD:
MACD: 15.34
Signal: 18.22
Histogram: -2.88 (bearish)

📊 EMA:
EMA20: $45,300.00
EMA50: $45,800.00
Trend: BEARISH
✨ GOLDEN CROSS DETECTED!

📊 Volume:
Current: 1,234,567.89
Avg (20): 987,654.32
Ratio: 1.25x (HIGH)

🎯 Signal: 🟢 STRONG BUY
```

---

### 2. `/scan`

Quick scan of all major coins (BTC, ETH, SOL, ZEC) on both 5m and 4h timeframes.

**Example Output:**
```
📊 MARKET SCAN RESULTS
━━━━━━━━━━━━━━━━━━

BTC $45,234.56 ✨
5m: 🟢 Strong Buy
4h: 🟢 Buy

ETH $2,345.67
5m: ⚪ Neutral
4h: ⚪ Neutral

SOL $139.45 ☠️
5m: 🔴 Sell
4h: 🔴🔴 Strong Sell

ZEC $45.67
5m: 🟢 Buy
4h: ⚪ Neutral

⏰ 16:45:30
```

**Markers:**
- ✨ = Golden Cross detected
- ☠️ = Death Cross detected

---

### 3. `/signals`

Get only actionable buy/sell signals (filters out neutral markets).

**Example Output:**
```
🎯 TRADING SIGNALS
━━━━━━━━━━━━━━━━━━

🟢🟢 STRONG BUY:
• BTC $45,234.56 (Both Timeframes)

🟢 BUY:
• ETH $2,345.67 (5m Only)

🔴 SELL:
• SOL $139.45 (4h Only)

⏰ 16:45:30

💡 Use /analyze <COIN> for detailed analysis
```

**Confirmation Types:**
- **Both Timeframes** - 5m and 4h agree (stronger signal)
- **5m Only** - Strong signal on 5m chart
- **4h Only** - Strong signal on 4h chart

---

## 🔧 Installation

### 1. Install Dependencies

```bash
pip install pandas numpy
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Run the Bot

```bash
python telegram_bot_standalone.py
```

---

## 📊 How Signals Are Generated

### Signal Scoring System:

The bot uses a multi-indicator scoring system:

**RSI Contribution:**
- RSI < 30: +2 points (oversold, buy signal)
- RSI < 40: +1 point (buy signal)
- RSI > 70: -2 points (overbought, sell signal)
- RSI > 60: -1 point (sell signal)

**MACD Contribution:**
- Positive histogram: +1 point (bullish)
- Negative histogram: -1 point (bearish)

**EMA Cross Contribution:**
- Golden Cross: +2 points (strong bullish)
- Death Cross: -2 points (strong bearish)

**Volume Amplifier:**
- High volume (>1.5x average): Multiplies score by 1.2

**Final Signal:**
- Score ≥ 3: **Strong Buy** 🟢🟢
- Score ≥ 1: **Buy** 🟢
- Score ≤ -3: **Strong Sell** 🔴🔴
- Score ≤ -1: **Sell** 🔴
- Otherwise: **Neutral** ⚪

---

## 💡 Trading Tips

### 1. **Timeframe Confirmation**
   - Best signals occur when both 5m and 4h agree
   - 4h signals are more reliable for swing trades
   - 5m signals are better for scalping

### 2. **Golden/Death Cross**
   - Golden Cross (✨): EMA20 crosses above EMA50 - **Bullish**
   - Death Cross (☠️): EMA20 crosses below EMA50 - **Bearish**
   - These are strong trend reversal signals

### 3. **Volume Confirmation**
   - High volume signals are more reliable
   - Low volume may indicate weak momentum

### 4. **RSI Levels**
   - RSI < 30: Oversold (potential bounce)
   - RSI > 70: Overbought (potential pullback)
   - RSI 40-60: Neutral zone

### 5. **Use Multiple Confirmations**
   - Don't rely on a single indicator
   - Look for multiple signals aligning
   - Check both timeframes before entering

---

## ⚠️ Disclaimer

**This is for educational purposes only!**

- Technical analysis is not guaranteed to be accurate
- Past performance doesn't predict future results
- Always do your own research (DYOR)
- Never invest more than you can afford to lose
- Use proper risk management and stop losses

---

## 🔄 Update Frequency

- Data is fetched in **real-time** from CoinDCX public API
- No authentication required for technical analysis
- Analysis is performed on-demand when you run commands
- Recommended: Run `/scan` or `/signals` every 5-15 minutes

---

## 🛠️ Customization

To analyze different coins, edit the market list in:

```python
# In telegram_bot_standalone.py

# Current coins
markets = ['B-BTC_USDT', 'B-ETH_USDT', 'B-SOL_USDT', 'B-ZEC_USDT']

# Add more coins
markets = ['B-BTC_USDT', 'B-ETH_USDT', 'B-SOL_USDT', 'B-ZEC_USDT', 'B-DOGE_USDT', 'B-XRP_USDT']
```

To change timeframes:

```python
# Analyze different timeframes
intervals = ['5m', '4h']  # Current
intervals = ['15m', '1h', '4h']  # Custom
```

---

## 🐛 Troubleshooting

### "Failed to fetch data"
- Check your internet connection
- CoinDCX API may be temporarily down
- Try a different coin/timeframe

### "Not enough data"
- Some new coins may have limited historical data
- Try increasing the limit in `get_candles()` method

### Slow response
- Analysis requires fetching 200+ candles per request
- Normal response time: 2-5 seconds
- If slower, check network latency

---

## 📈 Example Trading Workflow

1. **Morning Scan**
   ```
   /scan
   ```
   Check overall market conditions

2. **Detailed Analysis**
   ```
   /analyze BTC 4h
   ```
   Deep dive into specific opportunities

3. **Get Actionable Signals**
   ```
   /signals
   ```
   Find immediate trading opportunities

4. **Periodic Updates**
   - Run `/scan` every 15 minutes
   - Set alerts for golden/death crosses
   - Monitor high-volume signals

5. **Confirmation**
   - Check both timeframes
   - Look for volume confirmation
   - Verify with other tools/sources

Happy Trading! 🚀
