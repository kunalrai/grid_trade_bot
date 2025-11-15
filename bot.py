#!/usr/bin/env python3
"""
SOL/USDT Grid Trading Bot for Binance Futures
Main entry point
"""
import os
import json
from dotenv import load_dotenv
from logger import TradingLogger
from binance_client import BinanceFuturesClient
from grid_trader import GridTrader


def load_config(config_file: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {str(e)}")
        exit(1)


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()

    # Get API credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        print("Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")
        print("Please copy .env.example to .env and fill in your credentials")
        exit(1)

    # Load configuration
    config = load_config()

    # Initialize logger
    logger = TradingLogger()

    # Initialize Binance client
    # Set testnet=True for testing with Binance testnet
    client = BinanceFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        testnet=False,  # Change to True for testnet
        logger=logger
    )

    # Initialize and run grid trader
    trader = GridTrader(client, config, logger)
    trader.run()


if __name__ == "__main__":
    main()
