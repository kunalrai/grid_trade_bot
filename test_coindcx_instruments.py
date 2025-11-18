"""
Test script for fetching CoinDCX active USDT instruments
"""

import sys
import io
import requests
import json

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fetch_usdt_instruments():
    """Fetch active USDT instruments from CoinDCX"""
    print("=" * 60)
    print("CoinDCX Active USDT Instruments Test")
    print("=" * 60)
    print()

    # API endpoint for USDT instruments
    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments?margin_currency_short_name[]=USDT"

    try:
        print("📡 Fetching data from CoinDCX API...")
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return None

        instruments = response.json()

        if not instruments:
            print("❌ No instruments found")
            return None

        print(f"✅ Successfully fetched {len(instruments)} instruments\n")

        # Display first 20 instruments
        print("First 20 instruments:")
        print("-" * 60)
        for i, instrument in enumerate(instruments[:20], 1):
            print(f"{i:2d}. {instrument}")

        if len(instruments) > 20:
            print(f"\n... and {len(instruments) - 20} more instruments")

        print("\n" + "=" * 60)
        print(f"Total: {len(instruments)} active USDT instruments")
        print("=" * 60)

        # Save to file for reference
        output_file = "coindcx_usdt_instruments.json"
        with open(output_file, 'w') as f:
            json.dump(instruments, f, indent=2)
        print(f"\n💾 Full list saved to: {output_file}")

        return instruments

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def fetch_inr_instruments():
    """Fetch active INR instruments from CoinDCX"""
    print("\n" + "=" * 60)
    print("CoinDCX Active INR Instruments Test")
    print("=" * 60)
    print()

    # API endpoint for INR instruments
    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments?margin_currency_short_name[]=INR"

    try:
        print("📡 Fetching data from CoinDCX API...")
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return None

        instruments = response.json()

        if not instruments:
            print("❌ No instruments found")
            return None

        print(f"✅ Successfully fetched {len(instruments)} instruments\n")

        # Display all INR instruments (usually fewer)
        print("INR instruments:")
        print("-" * 60)
        for i, instrument in enumerate(instruments, 1):
            print(f"{i:2d}. {instrument}")

        print("\n" + "=" * 60)
        print(f"Total: {len(instruments)} active INR instruments")
        print("=" * 60)

        return instruments

    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    # Test USDT instruments
    usdt_instruments = fetch_usdt_instruments()

    # Test INR instruments
    inr_instruments = fetch_inr_instruments()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Start your trading bot: python backend/api_server.py")
    print("2. Open Telegram and message your bot")
    print("3. Send command: /instruments")
    print("4. You should see the list of active USDT instruments")
    print("\nNote: Make sure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in .env")
    print("=" * 60)
