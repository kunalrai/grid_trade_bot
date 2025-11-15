"""
Binance API client for perpetual futures trading
"""
import ccxt
from typing import Optional, Dict, Any
from logger import TradingLogger


class BinanceFuturesClient:
    """Handles Binance Futures API interactions"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False, logger: Optional[TradingLogger] = None):
        """
        Initialize Binance Futures client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet if True
            logger: TradingLogger instance
        """
        self.logger = logger
        self.testnet = testnet

        # Initialize CCXT Binance futures client
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })

        if testnet:
            self.exchange.set_sandbox_mode(True)
            if self.logger:
                self.logger.info("Using Binance Futures TESTNET")

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            self.exchange.fetch_balance()
            if self.logger:
                self.logger.info("✓ Binance API connection successful")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"✗ Binance API connection failed: {str(e)}")
            return False

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price

        Args:
            symbol: Trading pair symbol (e.g., 'SOL/USDT')

        Returns:
            Current price or None if error
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching price: {str(e)}")
            return None

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for the trading pair

        Args:
            symbol: Trading pair symbol
            leverage: Leverage amount (1-125)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            if self.logger:
                self.logger.info(f"Leverage set to {leverage}x for {symbol}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error setting leverage: {str(e)}")
            return False

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current position for the symbol

        Args:
            symbol: Trading pair symbol

        Returns:
            Position information or None
        """
        try:
            positions = self.exchange.fetch_positions([symbol])
            for position in positions:
                if position['symbol'] == symbol and float(position['contracts']) != 0:
                    return {
                        'size': float(position['contracts']),
                        'side': position['side'],
                        'entry_price': float(position['entryPrice']),
                        'unrealized_pnl': float(position['unrealizedPnl']),
                        'liquidation_price': float(position.get('liquidationPrice', 0))
                    }
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching position: {str(e)}")
            return None

    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict[str, Any]]:
        """
        Place a market order

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in base currency

        Returns:
            Order information or None if error
        """
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            if self.logger:
                self.logger.info(f"Market {side} order placed: {amount} {symbol}")
            return order
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error placing market order: {str(e)}")
            return None

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a limit order

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in base currency
            price: Limit price

        Returns:
            Order information or None if error
        """
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            if self.logger:
                self.logger.info(f"Limit {side} order placed: {amount} {symbol} @ ${price:.2f}")
            return order
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error placing limit order: {str(e)}")
            return None

    def cancel_all_orders(self, symbol: str) -> bool:
        """
        Cancel all open orders for the symbol

        Args:
            symbol: Trading pair symbol

        Returns:
            True if successful, False otherwise
        """
        try:
            self.exchange.cancel_all_orders(symbol)
            if self.logger:
                self.logger.info(f"All orders cancelled for {symbol}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error cancelling orders: {str(e)}")
            return False

    def get_balance(self) -> Optional[Dict[str, float]]:
        """
        Get account balance

        Returns:
            Balance information or None
        """
        try:
            balance = self.exchange.fetch_balance()
            return {
                'USDT': float(balance['USDT']['free']) if 'USDT' in balance else 0.0,
                'total_USDT': float(balance['USDT']['total']) if 'USDT' in balance else 0.0
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching balance: {str(e)}")
            return None
