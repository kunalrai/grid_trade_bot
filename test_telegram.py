"""
Test script for Telegram bot functionality
Run this to verify your Telegram bot is working before running the full trading bot
"""

import os
import asyncio
import logging
from telegram_notifier import TelegramNotifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_telegram_bot():
    """Test Telegram bot functionality"""

    print("=" * 60)
    print("TELEGRAM BOT TEST")
    print("=" * 60)

    # Get credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("❌ ERROR: Telegram credentials not found!")
        print("\nPlease set the following environment variables:")
        print("  - TELEGRAM_BOT_TOKEN")
        print("  - TELEGRAM_CHAT_ID")
        print("\nSee TELEGRAM_SETUP.md for instructions")
        return

    print(f"✅ Bot Token found: {bot_token[:10]}...")
    print(f"✅ Chat ID found: {chat_id}")
    print()

    # Create notifier
    notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id, logger=logger)

    if not notifier.enabled:
        print("❌ Telegram notifier could not be initialized")
        return

    print("Testing Telegram notifications...")
    print()

    # Test 1: Simple message
    print("Test 1: Sending simple message...")
    success = await notifier.send_message("🧪 Test message from Grid Trading Bot!")
    if success:
        print("✅ Simple message sent successfully")
    else:
        print("❌ Failed to send simple message")

    await asyncio.sleep(1)

    # Test 2: Trade notification
    print("\nTest 2: Sending trade notification...")
    await notifier.notify_trade('BUY', 10.5, 139.50, 'SOLUSDT')
    print("✅ Trade notification sent")

    await asyncio.sleep(1)

    # Test 3: Position update
    print("\nTest 3: Sending position update...")
    await notifier.notify_position_update(
        position_size=10.5,
        entry_price=139.50,
        current_price=143.20,
        pnl=38.85,
        pnl_percentage=2.65
    )
    print("✅ Position update sent")

    await asyncio.sleep(1)

    # Test 4: Error notification
    print("\nTest 4: Sending error notification...")
    await notifier.notify_error("This is a test error - everything is OK!")
    print("✅ Error notification sent")

    await asyncio.sleep(1)

    # Test 5: Daily summary
    print("\nTest 5: Sending daily summary...")
    await notifier.notify_daily_summary(trades=15, pnl=125.50, win_rate=73.3)
    print("✅ Daily summary sent")

    print()
    print("=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print()
    print("Check your Telegram app to see the test messages.")
    print("If you received all 5 messages, your Telegram bot is working correctly!")
    print()
    print("You can now start your trading bot and receive real-time notifications.")


if __name__ == "__main__":
    try:
        asyncio.run(test_telegram_bot())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
