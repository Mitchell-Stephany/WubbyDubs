#!/usr/bin/env python3
"""
Setup script for Price Arbitrage Tracker
Helps users configure and test their setup
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[X] Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"[OK] Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import requests
        import discord
        import bs4
        import apscheduler
        import ebaysdk
        print("[OK] All dependencies are installed")
        return True
    except ImportError as e:
        print(f"[X] Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    if not env_file.exists():
        print("[X] .env file not found")
        print("Copy .env.example to .env and fill in your credentials:")
        print("cp .env.example .env")
        return False
    
    print("[OK] .env file exists")
    
    # Check for required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN'),
        'DISCORD_CHANNEL_ID': os.getenv('DISCORD_CHANNEL_ID'),
        'EBAY_APP_ID': os.getenv('EBAY_APP_ID'),
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        print(f"[!] Missing environment variables: {', '.join(missing)}")
        print("Please fill these in your .env file")
        return False
    
    print("[OK] Required environment variables are set")
    return True

def test_database():
    """Test database creation"""
    from database import Database
    from exceptions import DatabaseError

    test_db = 'test_setup.db'
    try:
        Database(test_db)
        print("[OK] Database initialization successful")
        return True
    except DatabaseError as exc:
        print(f"[X] Database error: {exc}")
        return False
    finally:
        # Clean up test database
        try:
            os.remove(test_db)
        except OSError as exc:
            print(f"[!] Could not remove {test_db}: {exc}")

def test_discord_connection():
    """Test Discord bot connection (optional)"""
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')

    if not token or token == 'your_discord_bot_token_here':
        print("[!] Discord bot token not configured, skipping connection test")
        return True

    if not channel_id or channel_id == 'your_channel_id_here':
        print("[!] Discord channel ID not configured, skipping connection test")
        return True

    if not channel_id.isdigit():
        print(f"[X] DISCORD_CHANNEL_ID must be numeric, got {channel_id!r}")
        return False

    print("[!] Discord credentials configured - connection will be tested when running main application")
    return True

def main():
    """Run all setup checks"""
    print("=" * 50)
    print("Price Arbitrage Tracker - Setup Check")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Database", test_database),
        ("Discord Connection", test_discord_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("Setup Summary")
    print("=" * 50)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[SUCCESS] Setup is complete! You can run the application with:")
        print("python main.py")
    else:
        print("\n[WARNING] Some checks failed. Please fix the issues above.")
        print("For help, see README.md")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
