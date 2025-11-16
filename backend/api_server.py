"""
Flask API Server for Grid Trading Bot
Provides REST API and WebSocket for bot control and monitoring
"""
import os
import sys
import json
import threading
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
app = Flask(__name__)
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
    global trader
    if trader:
        status = trader.get_status()
        socketio.emit('status_update', status)


def run_bot_loop():
    """Run the trading bot in a separate thread"""
    global trader
    if trader:
        try:
            trader.run()
        except Exception as e:
            if logger:
                logger.error(f"Bot error: {str(e)}")


# ============== API ENDPOINTS ==============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    global config
    if config:
        return jsonify(config)
    return jsonify({'error': 'Configuration not loaded'}), 500


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

        if not api_key or not api_secret:
            return jsonify({'error': 'API credentials not configured'}), 400

        # Initialize CoinDCX client
        client = CoinDCXFuturesClient(
            api_key=api_key,
            api_secret=api_secret,
            logger=logger
        )

        # Initialize trader
        trader = GridTraderCoinDCX(client, config, logger)

        # Start bot in separate thread
        trader_thread = threading.Thread(target=run_bot_loop, daemon=True)
        trader_thread.start()

        return jsonify({
            'success': True,
            'message': 'Bot started successfully',
            'status': trader.get_status()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
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
    """Get current market price"""
    global trader

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        market = request.args.get('market', config['trading']['market'])
        price = trader.client.get_current_price(market)

        if price:
            return jsonify({
                'market': market,
                'price': price,
                'timestamp': datetime.now().isoformat()
            })
        return jsonify({'error': 'Failed to fetch price'}), 500
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

    if not trader or not trader.client:
        return jsonify({'error': 'Bot not initialized'}), 400

    try:
        wallet_details = trader.client.get_wallet_details()
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
    print("Server starting on http://localhost:5000")
    print("WebSocket available at ws://localhost:5000")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
