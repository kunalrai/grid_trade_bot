"""
CoinDCX API client for perpetual futures trading
"""
import hmac
import hashlib
import base64
import json
import time
import requests
from typing import Optional, Dict, Any, List
from logger import TradingLogger


class CoinDCXFuturesClient:
    """Handles CoinDCX Futures API interactions"""

    def __init__(self, api_key: str, api_secret: str, logger: Optional[TradingLogger] = None):
        """
        Initialize CoinDCX Futures client

        Args:
            api_key: CoinDCX API key
            api_secret: CoinDCX API secret
            logger: TradingLogger instance
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coindcx.com"
        self.public_url = "https://public.coindcx.com"
        self.logger = logger
        self.session = requests.Session()

    def _generate_signature(self, payload: str) -> str:
        """
        Generate HMAC signature for authentication

        Args:
            payload: JSON payload string

        Returns:
            HMAC signature
        """
        secret_bytes = bytes(self.api_secret, encoding='utf-8')
        payload_bytes = bytes(payload, encoding='utf-8')
        signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
        return signature

    def _get_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate request headers with authentication

        Args:
            payload: Request payload

        Returns:
            Headers dictionary
        """
        json_payload = json.dumps(payload, separators=(',', ':'))
        signature = self._generate_signature(json_payload)

        return {
            'Content-Type': 'application/json',
            'X-AUTH-APIKEY': self.api_key,
            'X-AUTH-SIGNATURE': signature
        }

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None,
                     public: bool = False) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to CoinDCX API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            payload: Request payload
            public: Use public URL if True

        Returns:
            Response data or None on error
        """
        url = f"{self.public_url if public else self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, timeout=10)
            else:
                headers = self._get_headers(payload) if payload else {}
                response = self.session.post(url, json=payload, headers=headers, timeout=10)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"API request failed: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            result = self.get_account_info()
            if result:
                if self.logger:
                    self.logger.info("✓ CoinDCX API connection successful")
                return True
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"✗ CoinDCX API connection failed: {str(e)}")
            return False

    def get_markets(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all available markets

        Returns:
            List of market information
        """
        return self._make_request("GET", "/exchange/v1/markets", public=True)

    def get_ticker(self, market: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker for specific market

        Args:
            market: Market symbol (e.g., 'B-SOL_USDT')

        Returns:
            Ticker data
        """
        result = self._make_request("GET", "/exchange/ticker", public=True)
        if result:
            for ticker in result:
                if ticker.get('market') == market:
                    return ticker
        return None

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information

        Returns:
            Account details (first user object from array response)
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/users/info", payload)

        # API returns an array, extract the first element
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        return result

    def get_balance(self) -> Optional[Dict[str, float]]:
        """
        Get account balance

        Returns:
            Balance information
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/users/balances", payload)

        if result:
            balances = {}
            for item in result:
                currency = item.get('currency')
                balance = float(item.get('balance', 0))
                balances[currency] = balance
            return balances
        return None

    def get_futures_balance(self) -> Optional[Dict[str, Any]]:
        """
        Get futures wallet balance

        Returns:
            Futures balance information
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }
        return self._make_request("POST", "/exchange/v1/wallet/balance", payload)

    def get_wallet_details(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get futures wallet details including all balances and locked amounts

        Returns:
            List of wallet details with balance information
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }

        # Note: This endpoint uses GET method but still requires authentication
        url = f"{self.base_url}/exchange/v1/derivatives/futures/wallets"

        try:
            json_payload = json.dumps(payload, separators=(',', ':'))
            signature = self._generate_signature(json_payload)

            headers = {
                'Content-Type': 'application/json',
                'X-AUTH-APIKEY': self.api_key,
                'X-AUTH-SIGNATURE': signature
            }

            response = self.session.get(url, data=json_payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"API request failed: {str(e)}")
            return None

    def transfer_to_futures(self, currency: str, amount: float) -> bool:
        """
        Transfer funds from spot to futures wallet

        Args:
            currency: Currency code (e.g., 'USDT')
            amount: Amount to transfer

        Returns:
            True if successful
        """
        payload = {
            "timestamp": int(time.time() * 1000),
            "currency": currency,
            "amount": amount,
            "from_wallet": "spot",
            "to_wallet": "futures"
        }
        result = self._make_request("POST", "/exchange/v1/wallets/transfer", payload)

        if result and self.logger:
            self.logger.info(f"Transferred {amount} {currency} to futures wallet")
        return result is not None

    def create_futures_order(self, market: str, side: str, order_type: str,
                           quantity: float, price: Optional[float] = None,
                           leverage: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Create a futures order

        Args:
            market: Market symbol (e.g., 'SOLUSDT')
            side: 'buy' or 'sell'
            order_type: 'market_order' or 'limit_order'
            quantity: Order quantity
            price: Limit price (required for limit orders)
            leverage: Leverage (if supported)

        Returns:
            Order information or None
        """
        payload = {
            "side": side,
            "order_type": order_type,
            "market": market,
            "total_quantity": quantity,
            "timestamp": int(time.time() * 1000),
            "client_order_id": f"grid_{int(time.time() * 1000)}"
        }

        if order_type == "limit_order" and price:
            payload["price_per_unit"] = price

        if leverage:
            payload["leverage"] = leverage

        result = self._make_request("POST", "/exchange/v1/orders/create", payload)

        if result and self.logger:
            self.logger.info(f"Futures {side} order created: {quantity} {market} @ {price if price else 'market'}")

        return result

    def place_market_order(self, market: str, side: str, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Place a market order

        Args:
            market: Market symbol
            side: 'buy' or 'sell'
            quantity: Order quantity

        Returns:
            Order information
        """
        return self.create_futures_order(market, side, "market_order", quantity)

    def place_limit_order(self, market: str, side: str, quantity: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a limit order

        Args:
            market: Market symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price

        Returns:
            Order information
        """
        return self.create_futures_order(market, side, "limit_order", quantity, price)

    def get_active_orders(self, market: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get active orders

        Args:
            market: Market symbol (required)

        Returns:
            List of active orders
        """
        payload = {
            "market": market,
            "timestamp": int(time.time() * 1000)
        }

        return self._make_request("POST", "/exchange/v1/orders/active_orders", payload)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        payload = {
            "id": order_id,
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/orders/cancel", payload)

        if result and self.logger:
            self.logger.info(f"Order {order_id} cancelled")

        return result is not None

    def cancel_all_orders(self, market: str) -> bool:
        """
        Cancel all open orders for a market

        Args:
            market: Market symbol

        Returns:
            True if successful
        """
        active_orders = self.get_active_orders(market)
        if not active_orders:
            return True

        for order in active_orders:
            self.cancel_order(order['id'])

        if self.logger:
            self.logger.info(f"All orders cancelled for {market}")
        return True

    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all open positions

        Returns:
            List of positions
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }
        return self._make_request("POST", "/exchange/v1/positions/list", payload)

    def get_position(self, market: str) -> Optional[Dict[str, Any]]:
        """
        Get position for specific market

        Args:
            market: Market symbol

        Returns:
            Position information or None
        """
        positions = self.get_positions()
        if positions:
            for pos in positions:
                if pos.get('market') == market and float(pos.get('quantity', 0)) != 0:
                    return {
                        'market': pos['market'],
                        'size': float(pos['quantity']),
                        'side': pos['side'],
                        'entry_price': float(pos.get('entry_price', 0)),
                        'unrealized_pnl': float(pos.get('unrealized_pnl', 0)),
                        'leverage': int(pos.get('leverage', 1))
                    }
        return None

    def exit_position(self, pair: str) -> bool:
        """
        Exit position using CoinDCX exit position API

        Args:
            pair: Trading pair (e.g., 'SOLUSDT')

        Returns:
            True if successful
        """
        payload = {
            "pair": pair,
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/positions/exit", payload)

        if result and self.logger:
            self.logger.info(f"Position exited for {pair}")

        return result is not None

    def close_position(self, market: str) -> bool:
        """
        Close position for market (using exit position API first, fallback to market order)

        Args:
            market: Market symbol

        Returns:
            True if successful
        """
        # Try using the exit position API first
        if self.exit_position(market):
            return True

        # Fallback: Place opposite order to close position
        position = self.get_position(market)
        if not position:
            return True

        side = 'sell' if position['side'] == 'long' else 'buy'
        quantity = abs(position['size'])

        result = self.place_market_order(market, side, quantity)
        return result is not None

    def get_order_history(self, market: Optional[str] = None, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """
        Get order history

        Args:
            market: Filter by market (optional)
            limit: Number of orders to retrieve

        Returns:
            List of historical orders
        """
        payload = {
            "timestamp": int(time.time() * 1000),
            "limit": limit
        }
        if market:
            payload["market"] = market

        return self._make_request("POST", "/exchange/v1/orders/list", payload)

    def get_current_price(self, market: str) -> Optional[float]:
        """
        Get current market price

        Args:
            market: Market symbol

        Returns:
            Current price or None
        """
        ticker = self.get_ticker(market)
        if ticker:
            return float(ticker.get('last_price', 0))
        return None

    def set_leverage(self, market: str, leverage: int) -> bool:
        """
        Set leverage for a market

        Args:
            market: Market symbol
            leverage: Leverage value

        Returns:
            True if successful
        """
        payload = {
            "market": market,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/positions/leverage", payload)

        if result and self.logger:
            self.logger.info(f"Leverage set to {leverage}x for {market}")

        return result is not None
