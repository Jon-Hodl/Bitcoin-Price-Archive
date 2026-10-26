#!/usr/bin/env python3
"""
BTC Price Database Updater
Fetches latest Bitcoin prices from mempool.space API
Optimized for daily incremental updates
"""

import json
import urllib.request
import ssl
from datetime import datetime, timedelta
import os

PRICES_FILE = 'prices.json'
MEMPOOL_API = 'https://mempool.space/api/v1/historical-price'

def fetch_json(url):
    """Fetch JSON from API with SSL context"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_None
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        return json.loads(response.read().decode())

def load_prices():
    """Load existing price data"""
    if not os.path.exists(PRICES_FILE):
        return {}
    
    with open(PRICES_FILE, 'r') as f:
        return json.load(f)

def save_prices(prices):
    """Save price data to JSON"""
    with open(PRICES_FILE, 'w') as f:
        json.dump(prices, f, indent=2)
    
    print(f"✓ Saved {len(prices)} price records to {PRICES_FILE}")

def fetch_latest_prices():
    """Fetch all prices from mempool.space (API returns full history efficiently)"""
    print("Fetching latest prices from mempool.space...")
    
    try:
        data = fetch_json(MEMPOOL_API)
        
        prices = {}
        for item in data.get('prices', []):
            # Convert timestamp to date string
            timestamp = item.get('time', 0)
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            # Store OHLC data
            prices[date] = {
                'o': item.get('USD', {}).get('open', 0),
                'h': item.get('USD', {}).get('high', 0),
                'l': item.get('USD', {}).get('low', 0),
                'c': item.get('USD', {}).get('close', 0)
            }
        
        return prices
    
    except Exception as e:
        print(f"✗ Error fetching prices: {e}")
        return None

def update_prices():
    """Main update function - optimized for daily incremental updates"""
    print("=" * 60)
    print("📊 BTC Price Database Updater")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    
    # Load existing prices
    existing_prices = load_prices()
    existing_count = len(existing_prices)
    print(f"📁 Loaded {existing_count:,} existing records")
    
    if existing_count > 0:
        latest_date = max(existing_prices.keys())
        print(f"📅 Latest data: {latest_date}")
    
    # Fetch new prices
    new_prices = fetch_latest_prices()
    
    if new_prices is None:
        print("✗ Failed to fetch prices")
        return 1
    
    # Merge with existing (new data takes precedence for updates)
    merged_prices = {**existing_prices, **new_prices}
    
    # Sort by date
    sorted_prices = dict(sorted(merged_prices.items()))
    new_count = len(sorted_prices)
    
    # Check for changes
    added = new_count - existing_count
    
    if added > 0:
        print(f"✨ Added {added} new price record(s)")
        dates = list(sorted_prices.keys())
        print(f"📈 Now covering: {dates[0]} to {dates[-1]}")
        print(f"💾 Total records: {new_count:,}")
    else:
        print("⏹  No new data (already up to date)")
    
    # Save updated prices
    save_prices(sorted_prices)
    
    print("=" * 60)
    print("✅ Update complete!")
    return 0 if added > 0 else 0

if __name__ == '__main__':
    exit(update_prices())
