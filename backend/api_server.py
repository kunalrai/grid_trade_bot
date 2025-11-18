"""
Flask API Server for Grid Trading Bot
Provides REST API and WebSocket for bot control and monitoring
"""
import os
import sys
import json
import threading
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import TradingLogger
from coindcx_client import CoinDCXFuturesClient
from grid_trader_coindcx import GridTraderCoinDCX

# Load environment variables
load_dotenv()

# Initialize Flask app
# Set the frontend folder as the static folder and template folder
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
app = Flask(__name__,
            static_folder=frontend_dir,
            static_url_path='')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
trader = None
trader_thread = None
logger = None
config = None


def load_config(config_file: str = "../config.json") -> dict:
    """Load configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Try alternative path
        alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(alt_path, 'r') as f:
            return json.load(f)


def emit_status_update():
    """Emit bot status update via WebSocket"""
    global trader, config, logger
    try:
        if trader:
            status = trader.get_status()
            socketio.emit('status_update', status)
        else:
            # Bot not started yet - return basic status with current price
            if config:
                try:
                    api_key = os.getenv('COINDCX_API_KEY')
                    api_secret = os.getenv('COINDCX_API_SECRET')
                    if api_key and api_secret:
                        client = CoinDCXFuturesClient(api_key, api_secret, logger)
                        current_price = client.get_current_price(config['trading']['market'])
                        status = {
                            'state': 'stopped',
                            'is_running': False,
                            'current_price': current_price,
                            'total_trades': 0,
                            'winning_trades': 0,
                            'win_rate': 0,
                            'cumulative_pnl': 0,
                            'cycles_completed': 0,
                            'has_position': False,
                            'position': None,
                            'entry_price': None,
                            'recent_trades': []
                        }
                        socketio.emit('status_update', status)
                except Exception as e:
                    print(f"Error fetching price for stopped bot: {e}")
    except Exception as e:
        print(f"Error emitting status update: {e}")


def run_bot_loop():
    """Run the trading bot in a separate thread"""
    global trader
    print(f"[DEBUG] run_bot_loop started. trader exists: {trader is not None}")
    if trader:
        try:
            print(f"[DEBUG] About to call trader.run(). State: {trader.bot_state}, Running: {trader.is_running}")
            trader.run()
            print(f"[DEBUG] trader.run() completed. State: {trader.bot_state}, Running: {trader.is_running}")
        except Exception as e:
            print(f"[DEBUG] Exception in trader.run(): {str(e)}")
            import traceback
            traceback.print_exc()
            if logger:
                logger.error(f"Bot error: {str(e)}")


# ============== FRONTEND ROUTES ==============

@app.route('/')
def index():
    """Serve the main frontend page"""
    return app.send_static_file('index.html')


# ============== API ENDPOINTS ==============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and keep-alive"""
    global trader

    response = {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': datetime.now().isoformat(),
        'bot_running': trader.is_running if trader else False,
        'bot_state': trader.bot_state if trader else 'stopped'
    }

    return jsonify(response)


@app.route('/api/ping', methods=['GET', 'POST'])
def ping():
    """Lightweight ping endpoint for keep-alive"""
    return jsonify({
        'pong': True,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/test/connection', methods=['GET'])
def test_api_connection():
    """Test CoinDCX API connection"""
    try:
        api_key = os.getenv('COINDCX_API_KEY')
        api_secret = os.getenv('COINDCX_API_SECRET')

        # Check if credentials look like placeholders
        is_placeholder = (
            not api_key or
            not api_secret or
            'your_api_key_here' in api_key.lower() or
            'your_coindcx' in api_key.lower() or
            'your_api_secret_here' in api_secret.lower()
        )

        if is_placeholder:
            return jsonify({
                'success': False,
                'error': 'API credentials not configured in .env file',
                'message': 'Please update .env file with real CoinDCX API credentials',
                'credentials': {
                    'api_key_set': bool(api_key and 'your_' not in api_key.lower()),
                    'api_secret_set': bool(api_secret and 'your_' not in api_secret.lower())
                }
            }), 400

        # Create test client
        test_client = CoinDCXFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            logger=None
        )

        # Test 1: Get wallet details (GET request)
        wallet_result = test_client.get_wallet_details()

        # Test 2: Get account info (POST request)
        account_result = test_client.get_account_info()

        results = {
            'success': True,
            'tests': {
                'wallet_api': {
                    'success': wallet_result is not None,
                    'data': wallet_result if wallet_result else 'Failed'
                },
                'account_api': {
                    'success': account_result is not None,
                    'data': account_result if account_result else 'Failed'
                }
            },
            'credentials': {
                'api_key_set': bool(api_key),
                'api_secret_set': bool(api_secret),
                'api_key_prefix': api_key[:8] + '...' if api_key else None
            }
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    global config

    # Load config if not already loaded
    if not config:
        try:
            config = load_config()
        except Exception as e:
            return jsonify({'error': f'Failed to load config: {str(e)}'}), 500

    return jsonify(config)


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    global config
    try:
        new_config = request.json
        config.update(new_config)

        # Save to file
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get bot status"""
    global trader
    if trader:
        status = trader.get_status()
        return jsonify(status)
    return jsonify({
        'state': 'stopped',
        'is_running': False,
        'message': 'Bot not initialized'
    })


@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    global trader, trader_thread, logger, config

    if trader and trader.is_running:
        return jsonify({'error': 'Bot is already running'}), 400

    try:
        # Load configuration
        config = load_config()

        # Initialize logger
        logger = TradingLogger()

        # Get API credentials
        api_key = os.getenv('COINDCX_API_KEY')
        api_secret = os.getenv('COINDCX_API_SECRET')

        # Check if credentials look like placeholders
        is_placeholder = (
            not api_key or
            not api_secret or
            'your_api_key_here' in api_key.lower() or
            'your_coindcx' in api_key.lower() or
            'your_api_secret_here' in api_secret.lower()
        )

        if is_placeholder:
            return jsonify({
                'error': 'API credentials not configured',
                'message': 'Please update .env file with real CoinDCX API credentials',
                'hint': 'Get credentials from CoinDCX Settings > API Management'
            }), 400

        # Initialize CoinDCX client
        client = CoinDCXFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            logger=logger
        )

        # Initialize trader
        trader = GridTraderCoinDCX(client, config, logger)
        print(f"[DEBUG] Trader created. State: {trader.bot_state}, Running: {trader.is_running}")

        # Set state to initializing before starting thread
        trader.bot_state = "initializing"
        trader.is_running = True
        print(f"[DEBUG] State set to initializing. State: {trader.bot_state}, Running: {trader.is_running}")

        # Start bot in separate thread
        trader_thread = threading.Thread(target=run_bot_loop, daemon=True)
        trader_thread.start()
        print(f"[DEBUG] Thread started")

        return jsonify({
            'success': True,
            'message': 'Bot started successfully',
            'status': trader.get_status()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot gracefully"""
    global trader

    if not trader:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        trader.stop()
        return jsonify({
            'success': True,
            'message': 'Bot stopped successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/force-stop', methods=['POST'])
def force_stop_bot():
    """Force stop the trading bot (clears error states)"""
    global trader, trader_thread

    try:
        if trader:
            # Force stop the trader
            trader.force_stop()

            # Give it a moment to clean up
            import time
            time.sleep(0.5)

            # Clear the trader instance
            trader = None
            trader_thread = None

            return jsonify({
                'success': True,
                'message': 'Bot force stopped successfully'
            })
        else:
            # Even if trader is None, clear the thread
            trader_thread = None
            return jsonify({
                'success': True,
                'message': 'No active bot to stop'
            })
    except Exception as e:
        # On any error, still try to clear the trader
        trader = None
        trader_thread = None
        return jsonify({
            'success': True,
            'message': f'Bot force stopped with errors: {str(e)}'
        })


@app.route('/api/bot/pause', methods=['POST'])
def pause_bot():
    """Pause the trading bot"""
    global trader

    if not trader:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        trader.pause()
        return jsonify({
            'success': True,
            'message': 'Bot paused successfully',
            'status': trader.get_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/resume', methods=['POST'])
def resume_bot():
    """Resume the trading bot"""
    global trader

    if not trader:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        trader.resume()
        return jsonify({
            'success': True,
            'message': 'Bot resumed successfully',
            'status': trader.get_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/price', methods=['GET'])
def get_market_price():
    """Get current market price (works without authentication - uses public API)"""
    try:
        market = request.args.get('market')

        # If no market specified, try to get from config
        if not market and config:
            market = config.get('trading', {}).get('market', 'B-SOL_USDT')
        elif not market:
            market = 'B-SOL_USDT'  # Default

        # If trader is initialized, use its client
        if trader and trader.client:
            price = trader.client.get_current_price(market)
        else:
            # Use public API - no authentication needed
            import requests
            response = requests.get("https://public.coindcx.com/exchange/ticker", timeout=10)
            response.raise_for_status()
            tickers = response.json()

            price = None
            for ticker in tickers:
                if ticker.get('market') == market:
                    price = float(ticker.get('last_price', 0))
                    break

        if price:
            return jsonify({
                'market': market,
                'price': price,
                'timestamp': datetime.now().isoformat()
            })
        return jsonify({'error': f'Failed to fetch price for {market}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/account/balance', methods=['GET'])
def get_account_balance():
    """Get account balance"""
    global trader

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        balance = trader.client.get_futures_balance()
        return jsonify(balance if balance else {'error': 'Failed to fetch balance'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get all positions"""
    global trader

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        positions = trader.client.get_positions()
        return jsonify(positions if positions else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/active', methods=['GET'])
def get_active_orders():
    """Get active orders"""
    global trader

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        market = request.args.get('market')
        orders = trader.client.get_active_orders(market)
        return jsonify(orders if orders else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders/history', methods=['GET'])
def get_order_history():
    """Get order history"""
    global trader

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        market = request.args.get('market')
        limit = int(request.args.get('limit', 50))
        orders = trader.client.get_order_history(market, limit)
        return jsonify(orders if orders else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get bot trade history"""
    global trader

    if not trader:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        limit = int(request.args.get('limit', 50))
        trades = trader.trades[-limit:] if trader.trades else []

        # Convert datetime objects to ISO format
        serialized_trades = []
        for trade in trades:
            trade_copy = trade.copy()
            if isinstance(trade_copy.get('timestamp'), datetime):
                trade_copy['timestamp'] = trade_copy['timestamp'].isoformat()
            serialized_trades.append(trade_copy)

        return jsonify(serialized_trades)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get trading statistics"""
    global trader

    if not trader:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        status = trader.get_status()

        stats = {
            'total_trades': status['total_trades'],
            'winning_trades': status['winning_trades'],
            'losing_trades': status['total_trades'] - status['winning_trades'],
            'win_rate': status['win_rate'],
            'cumulative_pnl': status['cumulative_pnl'],
            'cycles_completed': status['cycles_completed'],
            'avg_profit_per_cycle': status['cumulative_pnl'] / status['cycles_completed'] if status['cycles_completed'] > 0 else 0
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/wallet/details', methods=['GET'])
def get_wallet_details():
    """Get detailed wallet information"""
    global trader

    try:
        # If bot is running, use existing client
        if trader and trader.client:
            wallet_details = trader.client.get_wallet_details()
        else:
            # Create a temporary client to fetch wallet details
            api_key = os.getenv('COINDCX_API_KEY')
            api_secret = os.getenv('COINDCX_API_SECRET')

            if not api_key or not api_secret:
                return jsonify({'error': 'API credentials not configured'}), 400

            # Create temporary client
            temp_client = CoinDCXFuturesClient(
                api_key=api_key,
                api_secret=api_secret,
                logger=None
            )
            wallet_details = temp_client.get_wallet_details()

        if wallet_details:
            return jsonify({
                'success': True,
                'wallet': wallet_details
            })
        return jsonify({'error': 'Failed to fetch wallet details'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent log entries"""
    global logger

    if not logger:
        return jsonify({'error': 'Logger not initialized'}), 400

    try:
        limit = int(request.args.get('limit', 100))
        # Get recent logs from logger
        logs = logger.get_recent_logs(limit) if hasattr(logger, 'get_recent_logs') else []

        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== WEBSOCKET EVENTS ==============

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit_status_update()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')


@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    emit_status_update()


# ============== BACKGROUND TASKS ==============

def background_status_broadcast():
    """Broadcast status updates every 5 seconds"""
    import time
    while True:
        time.sleep(5)
        emit_status_update()


# Start background task
status_thread = threading.Thread(target=background_status_broadcast, daemon=True)
status_thread.start()


if __name__ == '__main__':
    print("=" * 60)
    print("Grid Trading Bot - API Server")
    print("=" * 60)

    # Get port from environment variable for production deployment
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_ENV') != 'production'

    print(f"Server starting on http://0.0.0.0:{port}")
    print(f"WebSocket available at ws://0.0.0.0:{port}")
    print("=" * 60)

    # Load config at startup
    try:
        config = load_config()
        logger = TradingLogger()
        print("Configuration loaded successfully")

        # Auto-start bot if configured
        if config.get('monitoring', {}).get('auto_start_bot', False):
            print("\n🚀 Auto-starting trading bot...")
            try:
                # Initialize trader
                api_key = os.getenv('COINDCX_API_KEY')
                api_secret = os.getenv('COINDCX_API_SECRET')

                if not api_key or not api_secret:
                    print("⚠️  Warning: CoinDCX API credentials not found. Bot will not auto-start.")
                    print("   Set COINDCX_API_KEY and COINDCX_API_SECRET environment variables.")
                else:
                    client = CoinDCXFuturesClient(api_key, api_secret, logger)
                    trader = GridTraderCoinDCX(client, config, logger)

                    # Start bot in background thread
                    trader_thread = threading.Thread(target=trader.run, daemon=True)
                    trader_thread.start()
                    print("✅ Trading bot auto-started successfully!")
            except Exception as e:
                print(f"❌ Failed to auto-start bot: {e}")

    except Exception as e:
        print(f"Warning: Could not load config at startup: {e}")

    # Disable reloader to prevent port binding issues
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)
