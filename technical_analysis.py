"""
Technical Analysis Module
Provides indicators: RSI, MACD, EMA, Volume analysis, Golden/Death Cross detection
"""
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class TechnicalAnalyzer:
    """Handles technical analysis calculations and signal generation"""

    def __init__(self):
        self.base_url = "https://public.coindcx.com"

    def get_candles(self, market: str, interval: str = '5m', limit: int = 200) -> Optional[pd.DataFrame]:
        """
        Fetch candlestick data from CoinDCX

        Args:
            market: Market symbol (e.g., 'B-BTC_USDT', 'B-SOL_USDT')
            interval: Candle interval ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # CoinDCX candle endpoint
            url = f"{self.base_url}/market_data/candles"
            params = {
                'pair': market,
                'interval': interval,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)
            df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']

            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df = df.sort_values('time')

            return df

        except Exception as e:
            print(f"Error fetching candles: {e}")
            return None

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()

        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return macd, signal_line, histogram

    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()

    def detect_ema_cross(self, ema_short: pd.Series, ema_long: pd.Series) -> str:
        """
        Detect EMA crossover
        Returns: 'golden_cross', 'death_cross', or 'none'
        """
        # Check last 2 candles for crossover
        if len(ema_short) < 2 or len(ema_long) < 2:
            return 'none'

        prev_short = ema_short.iloc[-2]
        prev_long = ema_long.iloc[-2]
        curr_short = ema_short.iloc[-1]
        curr_long = ema_long.iloc[-1]

        # Golden Cross: short crosses above long
        if prev_short <= prev_long and curr_short > curr_long:
            return 'golden_cross'

        # Death Cross: short crosses below long
        if prev_short >= prev_long and curr_short < curr_long:
            return 'death_cross'

        return 'none'

    def analyze_volume(self, df: pd.DataFrame, period: int = 20) -> Dict:
        """Analyze volume trends"""
        avg_volume = df['volume'].tail(period).mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        return {
            'current': current_volume,
            'average': avg_volume,
            'ratio': volume_ratio,
            'status': 'high' if volume_ratio > 1.5 else 'normal' if volume_ratio > 0.7 else 'low'
        }

    def get_signal_strength(self, rsi: float, macd_histogram: float, ema_cross: str, volume_status: str) -> str:
        """
        Determine overall signal strength based on multiple indicators
        Returns: 'strong_buy', 'buy', 'neutral', 'sell', 'strong_sell'
        """
        score = 0

        # RSI scoring
        if rsi < 30:
            score += 2  # Oversold - strong buy signal
        elif rsi < 40:
            score += 1  # Buy signal
        elif rsi > 70:
            score -= 2  # Overbought - strong sell signal
        elif rsi > 60:
            score -= 1  # Sell signal

        # MACD scoring
        if macd_histogram > 0:
            score += 1  # Bullish
        else:
            score -= 1  # Bearish

        # EMA Cross scoring
        if ema_cross == 'golden_cross':
            score += 2
        elif ema_cross == 'death_cross':
            score -= 2

        # Volume confirmation
        if volume_status == 'high':
            score = score * 1.2  # Amplify signal with high volume

        # Determine signal
        if score >= 3:
            return 'strong_buy'
        elif score >= 1:
            return 'buy'
        elif score <= -3:
            return 'strong_sell'
        elif score <= -1:
            return 'sell'
        else:
            return 'neutral'

    def analyze_market(self, market: str, interval: str = '5m') -> Optional[Dict]:
        """
        Perform complete technical analysis on a market

        Args:
            market: Market symbol (e.g., 'B-BTC_USDT')
            interval: Candle interval

        Returns:
            Dictionary with all indicators and signals
        """
        df = self.get_candles(market, interval)
        if df is None or len(df) < 50:
            return None

        # Calculate indicators
        rsi = self.calculate_rsi(df)
        macd, signal_line, histogram = self.calculate_macd(df)
        ema20 = self.calculate_ema(df, 20)
        ema50 = self.calculate_ema(df, 50)
        volume_analysis = self.analyze_volume(df)
        ema_cross = self.detect_ema_cross(ema20, ema50)

        # Get current values
        current_price = df['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        current_ema20 = ema20.iloc[-1]
        current_ema50 = ema50.iloc[-1]

        # Determine signal strength
        signal = self.get_signal_strength(
            current_rsi,
            current_histogram,
            ema_cross,
            volume_analysis['status']
        )

        return {
            'market': market,
            'interval': interval,
            'timestamp': datetime.now().isoformat(),
            'price': {
                'current': current_price,
                'open': df['open'].iloc[-1],
                'high': df['high'].iloc[-1],
                'low': df['low'].iloc[-1]
            },
            'rsi': {
                'value': current_rsi,
                'status': 'oversold' if current_rsi < 30 else 'overbought' if current_rsi > 70 else 'neutral'
            },
            'macd': {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_histogram,
                'status': 'bullish' if current_histogram > 0 else 'bearish'
            },
            'ema': {
                'ema20': current_ema20,
                'ema50': current_ema50,
                'cross': ema_cross,
                'trend': 'bullish' if current_ema20 > current_ema50 else 'bearish'
            },
            'volume': volume_analysis,
            'signal': signal
        }

    def scan_multiple_markets(self, markets: List[str], intervals: List[str] = ['5m', '4h']) -> Dict:
        """
        Scan multiple markets across multiple timeframes

        Args:
            markets: List of market symbols
            intervals: List of timeframes to analyze

        Returns:
            Dictionary with analysis for each market and timeframe
        """
        results = {}

        for market in markets:
            results[market] = {}
            for interval in intervals:
                analysis = self.analyze_market(market, interval)
                if analysis:
                    results[market][interval] = analysis

        return results

    def get_trading_signals(self, markets: List[str], timeframes: List[str] = None) -> Dict:
        """
        Get consolidated trading signals for multiple markets
        Returns only markets with actionable signals (buy/sell)

        Args:
            markets: List of market symbols
            timeframes: List of timeframes to analyze (default: ['5m', '4h'])
        """
        if timeframes is None:
            timeframes = ['5m', '4h']

        signals = {
            'strong_buy': [],
            'buy': [],
            'strong_sell': [],
            'sell': [],
            'timestamp': datetime.now().isoformat()
        }

        scan_results = self.scan_multiple_markets(markets, timeframes)

        for market, intervals in scan_results.items():
            # Collect signals from all timeframes
            tf_signals = {}
            for tf in timeframes:
                tf_data = intervals.get(tf, {})
                tf_signals[tf] = tf_data.get('signal', 'neutral')

            # Count confirmations by signal type
            signal_counts = {
                'strong_buy': 0,
                'buy': 0,
                'neutral': 0,
                'sell': 0,
                'strong_sell': 0
            }

            for signal in tf_signals.values():
                if signal in signal_counts:
                    signal_counts[signal] += 1

            # Determine overall signal based on majority
            # Group buy signals
            buy_count = signal_counts['buy'] + signal_counts['strong_buy']
            sell_count = signal_counts['sell'] + signal_counts['strong_sell']

            overall_signal = None
            confirmation_count = 0

            if buy_count >= sell_count and buy_count > signal_counts['neutral']:
                if signal_counts['strong_buy'] >= signal_counts['buy']:
                    overall_signal = 'strong_buy'
                    confirmation_count = signal_counts['strong_buy']
                else:
                    overall_signal = 'buy'
                    confirmation_count = buy_count
            elif sell_count > buy_count and sell_count > signal_counts['neutral']:
                if signal_counts['strong_sell'] >= signal_counts['sell']:
                    overall_signal = 'strong_sell'
                    confirmation_count = signal_counts['strong_sell']
                else:
                    overall_signal = 'sell'
                    confirmation_count = sell_count

            # Add to signals if we have a clear direction
            if overall_signal and overall_signal in signals:
                signals[overall_signal].append({
                    'market': market,
                    'signal': overall_signal,
                    'confirmation_count': confirmation_count,
                    'total_timeframes': len(timeframes),
                    'timeframe_signals': tf_signals,
                    'timeframe_data': intervals
                })

        return signals

    def check_multi_timeframe_confirmation(self, market: str, timeframes: List[str],
                                           min_confirmations: int = 4,
                                           required_signal: str = 'buy') -> Dict:
        """
        Check if a market has sufficient multi-timeframe confirmation

        Args:
            market: Market symbol (e.g., 'B-SOL_USDT')
            timeframes: List of timeframes to check (e.g., ['5m', '15m', '1h', '2h', '4h', '1d'])
            min_confirmations: Minimum number of timeframes that must agree
            required_signal: Required signal type ('buy', 'strong_buy', 'sell', 'strong_sell')

        Returns:
            Dictionary with confirmation status and details
        """
        results = {}

        for tf in timeframes:
            analysis = self.analyze_market(market, tf)
            if analysis:
                results[tf] = {
                    'signal': analysis['signal'],
                    'rsi': analysis['rsi']['value'],
                    'macd_histogram': analysis['macd']['histogram'],
                    'ema_cross': analysis['ema']['cross'],
                    'volume_status': analysis['volume']['status'],
                    'price': analysis['price']['current']
                }

        # Count confirmations
        confirmations = 0
        buy_signals = ['buy', 'strong_buy']
        sell_signals = ['sell', 'strong_sell']

        if required_signal in buy_signals:
            target_signals = buy_signals
        elif required_signal in sell_signals:
            target_signals = sell_signals
        else:
            target_signals = [required_signal]

        for tf, data in results.items():
            if data['signal'] in target_signals:
                confirmations += 1

        confirmed = confirmations >= min_confirmations

        return {
            'confirmed': confirmed,
            'confirmations': confirmations,
            'required': min_confirmations,
            'total_timeframes': len(timeframes),
            'percentage': (confirmations / len(timeframes) * 100) if timeframes else 0,
            'timeframe_results': results,
            'overall_signal': required_signal if confirmed else 'insufficient'
        }
