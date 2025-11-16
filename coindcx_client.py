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
                if payload:
                    # CRITICAL: Generate JSON string for signature, then use SAME string as body
                    # This ensures signature matches the actual request body
                    json_payload = json.dumps(payload, separators=(',', ':'))
                    headers = self._get_headers(payload)
                    # Use 'data' parameter with the JSON string, NOT 'json' parameter
                    response = self.session.post(url, data=json_payload, headers=headers, timeout=10)
                else:
                    response = self.session.post(url, timeout=10)

            response.raise_for_status()
            result = response.json()

            # Log successful response for debugging (only if debug method exists)
            if self.logger and hasattr(self.logger, 'debug'):
                self.logger.debug(f"API {method} {endpoint} - Success")

            return result

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"API request failed: {method} {endpoint}")
                self.logger.error(f"Error: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_data = e.response.json()
                        self.logger.error(f"Response: {error_data}")
                    except:
                        self.logger.error(f"Response text: {e.response.text[:200]}")
            return None

    def test_connection(self) -> bool:
        """Test API connection using wallet endpoint (most reliable)"""
        try:
            # Use wallet details endpoint as it's more reliable than account info
            result = self.get_wallet_details()
            if result is not None:  # Even empty array is success
                if self.logger:
                    self.logger.info("✓ CoinDCX API connection successful")
                return True

            # Fallback to account info
            account_result = self.get_account_info()
            if account_result:
                if self.logger:
                    self.logger.info("✓ CoinDCX API connection successful (via account info)")
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
            Example response: {'coindcx_id': 'xxx', 'first_name': 'xxx', 'last_name': 'xxx',
                              'mobile_number': 'xxx', 'email': 'xxx@example.com'}
        """
        payload = {
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/users/info", payload)

        # API returns an array, extract the first element
        if result:
            if isinstance(result, list) and len(result) > 0:
                user_info = result[0]
                if self.logger:
                    self.logger.info(f"✓ Account authenticated: {user_info.get('email', 'unknown')}")
                return user_info
            elif isinstance(result, dict):
                # In case API format changes to return single object
                if self.logger:
                    self.logger.info(f"✓ Account authenticated: {result.get('email', 'unknown')}")
                return result

        if self.logger:
            self.logger.error("✗ Failed to get account info - API returned empty or invalid response")
        return None

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
        Create a futures order using CoinDCX futures API format

        Args:
            market: Market symbol (e.g., 'SOLUSDT' will be converted to 'B-SOL_USDT')
            side: 'buy' or 'sell'
            order_type: 'market_order' or 'limit_order'
            quantity: Order quantity
            price: Limit price (required for limit orders)
            leverage: Leverage (default 10x)

        Returns:
            Order information or None
        """
        # Convert market format: SOLUSDT -> B-SOL_USDT
        if not market.startswith('B-'):
            # Extract base and quote: SOLUSDT -> SOL, USDT
            # Assuming format is always BASEUSDT or BASEBUSD
            if 'USDT' in market:
                base = market.replace('USDT', '')
                quote = 'USDT'
            elif 'BUSD' in market:
                base = market.replace('BUSD', '')
                quote = 'BUSD'
            else:
                base = market[:-4]  # fallback
                quote = market[-4:]

            market = f"B-{base}_{quote}"

        # Build order object in CoinDCX format
        order_obj = {
            "side": side,
            "pair": market,
            "order_type": order_type,
            "total_quantity": quantity,
            "notification": "no_notification",
            "time_in_force": "good_till_cancel",
            "hidden": False,
            "post_only": False
        }

        # Add price for limit orders
        if order_type == "limit_order" and price:
            order_obj["price"] = str(price)
        elif order_type == "market_order":
            # Market orders may need a reference price
            order_obj["price"] = str(price) if price else "0"

        # Add leverage if specified
        if leverage:
            order_obj["leverage"] = leverage

        # Wrap in payload with timestamp
        payload = {
            "timestamp": int(time.time() * 1000),
            "order": order_obj
        }

        result = self._make_request("POST", "/exchange/v1/derivatives/futures/orders/create", payload)

        # Extract first element from array response
        if result and isinstance(result, list) and len(result) > 0:
            order_info = result[0]
            if self.logger:
                self.logger.info(f"Futures {side} order created: {quantity} {market} @ {price if price else 'market'} (ID: {order_info.get('id', 'unknown')})")
            return order_info

        return None

    def place_market_order(self, market: str, side: str, quantity: float,
                          price: Optional[float] = None, leverage: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Place a market order

        Args:
            market: Market symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Reference price for market order (optional)
            leverage: Leverage to use (optional)

        Returns:
            Order information
        """
        return self.create_futures_order(market, side, "market_order", quantity, price, leverage)

    def place_limit_order(self, market: str, side: str, quantity: float, price: float,
                         leverage: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Place a limit order

        Args:
            market: Market symbol
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price
            leverage: Leverage to use (optional)

        Returns:
            Order information
        """
        return self.create_futures_order(market, side, "limit_order", quantity, price, leverage)

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
            "timestamp": int(time.time() * 1000),
            "page": "1",
            "size": "100",
            "margin_currency_short_name": ["USDT"]
        }
        return self._make_request("POST", "/exchange/v1/derivatives/futures/positions", payload)

    def get_position(self, market: str) -> Optional[Dict[str, Any]]:
        """
        Get position for specific market

        Args:
            market: Market symbol (e.g., 'SOLUSDT' will match 'B-SOL_USDT')

        Returns:
            Position information or None
        """
        positions = self.get_positions()
        if positions:
            for pos in positions:
                # Match market: 'SOLUSDT' should match 'B-SOL_USDT'
                pair = pos.get('pair', '')
                # Convert B-SOL_USDT to SOLUSDT format for comparison
                normalized_pair = pair.replace('B-', '').replace('_', '')

                if normalized_pair == market and float(pos.get('active_pos', 0)) != 0:
                    active_pos = float(pos.get('active_pos', 0))

                    return {
                        'id': pos.get('id'),  # Position ID for exit API
                        'market': pair,
                        'size': abs(active_pos),
                        'side': 'long' if active_pos > 0 else 'short',
                        'entry_price': float(pos.get('avg_price', 0)),
                        'unrealized_pnl': 0,  # Not directly available in this response
                        'leverage': int(pos.get('leverage', 1)),
                        'liquidation_price': float(pos.get('liquidation_price', 0)),
                        'margin_type': pos.get('margin_type', 'crossed')
                    }
        return None

    def exit_position(self, position_id: str) -> bool:
        """
        Exit position using CoinDCX exit position API

        Args:
            position_id: Position ID to exit

        Returns:
            True if successful
        """
        payload = {
            "id": position_id,
            "timestamp": int(time.time() * 1000)
        }
        result = self._make_request("POST", "/exchange/v1/derivatives/futures/positions/exit", payload)

        if result and self.logger:
            self.logger.info(f"Position exited (ID: {position_id})")

        return result is not None

    def close_position(self, market: str) -> bool:
        """
        Close position for market (using exit position API first, fallback to market order)

        Args:
            market: Market symbol

        Returns:
            True if successful
        """
        # Get position to extract ID
        position = self.get_position(market)
        if not position:
            return True  # No position to close

        # Try using the exit position API first
        if position.get('id') and self.exit_position(position['id']):
            return True

        # Fallback: Place opposite order to close position
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

    # Note: CoinDCX sets leverage per-order, not per-position
    # Leverage is specified in the order payload when creating futures orders
    # See create_futures_order() method
