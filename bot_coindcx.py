#!/usr/bin/env python3
"""
SOL/USDT Grid Trading Bot for CoinDCX Futures
Main entry point - Standalone version
"""
import os
import json
from dotenv import load_dotenv
from logger import TradingLogger
from coindcx_client import CoinDCXFuturesClient
from grid_trader_coindcx import GridTraderCoinDCX


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
    api_key = os.getenv('COINDCX_API_KEY')
    api_secret = os.getenv('COINDCX_API_SECRET')

    if not api_key or not api_secret:
        print("Error: COINDCX_API_KEY and COINDCX_API_SECRET must be set in .env file")
        print("Please copy .env.example to .env and fill in your CoinDCX credentials")
        exit(1)

    # Load configuration
    config = load_config()

    # Initialize logger
    logger = TradingLogger()

    # Initialize CoinDCX client
    client = CoinDCXFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        logger=logger
    )

    # Initialize and run grid trader
    trader = GridTraderCoinDCX(client, config, logger)
    trader.run()


if __name__ == "__main__":
    main()
