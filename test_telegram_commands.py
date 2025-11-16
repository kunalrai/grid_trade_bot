"""
Quick test to verify Telegram bot responds to commands
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("TELEGRAM BOT COMMAND TEST")
print("=" * 60)

# Check credentials
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    print("❌ ERROR: Telegram credentials not found!")
    print("\nPlease set:")
    print("  - TELEGRAM_BOT_TOKEN")
    print("  - TELEGRAM_CHAT_ID")
    exit(1)

print(f"✅ Bot Token: {bot_token[:10]}...")
print(f"✅ Chat ID: {chat_id}")
print()

print("🤖 Instructions:")
print("=" * 60)
print("1. The bot should now be running (check your logs)")
print("2. Open Telegram and find your bot")
print("3. Send the following commands and verify responses:")
print()
print("   /help      - Should show list of commands")
print("   /status    - Should show bot status")
print("   /stats     - Should show trading statistics")
print()
print("If the bot responds to /help, it's working correctly!")
print()
print("Note: Make sure the trading bot is running with:")
print("  python backend/api_server.py")
print("=" * 60)
