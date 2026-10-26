#!/usr/bin/env python3
"""
BTC Price Database Updater
Fetches Bitcoin prices from mempool.space API and aggregates hourly
spot prices into daily OHLC (Open, High, Low, Close) records.
"""

import json
import urllib.request
import ssl
import os
from datetime import datetime, timezone

PRICES_FILE = 'prices.json'
MEMPOOL_API = 'https://mempool.space/api/v1/historical-price'


def fetch_json(url):
    """Fetch JSON from API with permissive SSL context."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
        return json.loads(response.read().decode())


def load_prices():
    """Load existing price data."""
    if not os.path.exists(PRICES_FILE):
        return {}

    with open(PRICES_FILE, 'r') as f:
        return json.load(f)


def save_prices(prices):
    """Save price data to JSON."""
    with open(PRICES_FILE, 'w') as f:
        json.dump(prices, f, indent=2)

    print(f"✓ Saved {len(prices):,} price records to {PRICES_FILE}")


def aggregate_daily_ohlc(prices_list):
    """Aggregate hourly spot prices into daily OHLC."""
    daily = {}

    # API returns newest first; reverse to process oldest first so open/close
    # are naturally first/last of each day.
    for item in reversed(prices_list):
        timestamp = item.get('time')
        if not timestamp:
            continue

        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d')
        price = item.get('USD')

        if price is None or price <= 0:
            continue

        if date not in daily:
            daily[date] = {
                'o': price,
                'h': price,
                'l': price,
                'c': price,
            }
        else:
            day = daily[date]
            day['h'] = max(day['h'], price)
            day['l'] = min(day['l'], price)
            day['c'] = price

    return daily


def fetch_latest_prices():
    """Fetch all prices from mempool.space and aggregate to daily OHLC."""
    print("Fetching latest prices from mempool.space...")

    try:
        data = fetch_json(MEMPOOL_API)
        return aggregate_daily_ohlc(data.get('prices', []))
    except Exception as e:
        print(f"✗ Error fetching prices: {e}")
        return None


def strip_volume(prices):
    """Remove volume field from all records."""
    for date, record in prices.items():
        record.pop('v', None)


def update_prices():
    """Main update function."""
    print("=" * 60)
    print("📊 BTC Price Database Updater")
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    existing_prices = load_prices()
    existing_count = len(existing_prices)
    print(f"📁 Loaded {existing_count:,} existing records")

    # Strip volume field from existing data (per project decision).
    strip_volume(existing_prices)

    if existing_count > 0:
        latest_date = max(existing_prices.keys())
        print(f"📅 Latest existing data: {latest_date}")

    new_prices = fetch_latest_prices()

    if new_prices is None:
        print("✗ Failed to fetch prices")
        return 1

    print(f"📥 Fetched {len(new_prices):,} daily records from mempool.space")

    # Merge: existing records take precedence for dates already present,
    # new dates are filled in from mempool.space data.
    merged_prices = dict(existing_prices)
    for date, record in new_prices.items():
        if date not in merged_prices:
            merged_prices[date] = record

    sorted_prices = dict(sorted(merged_prices.items()))
    new_count = len(sorted_prices)
    added = new_count - existing_count

    if added > 0:
        dates = list(sorted_prices.keys())
        print(f"✨ Added {added} new price record(s)")
        print(f"📈 Now covering: {dates[0]} to {dates[-1]}")
        print(f"💾 Total records: {new_count:,}")
    else:
        print("⏹  No new data (already up to date)")

    save_prices(sorted_prices)

    print("=" * 60)
    print("✅ Update complete!")
    return 0


if __name__ == '__main__':
    exit(update_prices())
