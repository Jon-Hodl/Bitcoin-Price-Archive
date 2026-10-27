#!/usr/bin/env python3
"""Pre-compute the default DCA scenario for the Bitcoin Price Archive.

Default matches the Dollar Cost Average Bitcoin calculator defaults:
  - $21 per purchase
  - weekly frequency
  - first buy 7 years ago from the latest price date
  - accumulate for 4 years
  - buy at the daily high (worst-case entry)
  - final value uses the latest daily low (worst-case exit)

Outputs dca-default.json with summary stats, weekly-sampled chart data,
and the full purchase history.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

PRICES_FILE = Path('prices.json')
OUTPUT_FILE = Path('dca-default.json')

AMOUNT = 21
FREQUENCY = 'weekly'
YEARS_AGO = 7
ACCUMULATE_YEARS = 4


def load_prices():
    with open(PRICES_FILE, 'r') as f:
        return json.load(f)


def add_years(date_obj, years):
    """Add years to a date, clamping Feb 29 -> Feb 28 when needed."""
    try:
        return date_obj.replace(year=date_obj.year + years)
    except ValueError:
        # Feb 29 in a non-leap year
        return date_obj.replace(year=date_obj.year + years, day=date_obj.day - 1)


def get_purchase_dates(start_str, end_str, frequency):
    """Generate purchase dates between start and end (inclusive)."""
    start = datetime.strptime(start_str, '%Y-%m-%d').date()
    end = datetime.strptime(end_str, '%Y-%m-%d').date()
    step = {
        'daily': timedelta(days=1),
        'weekly': timedelta(days=7),
        'biweekly': timedelta(days=14),
        'monthly': 'monthly',
    }[frequency]

    dates = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        if step == 'monthly':
            # Add one month, clamping day if needed
            try:
                current = current.replace(month=current.month + 1)
            except ValueError:
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    # e.g. Jan 31 -> Feb 28/29
                    next_month = current.month + 1
                    year = current.year
                    if next_month > 12:
                        next_month = 1
                        year += 1
                    current = current.replace(year=year, month=next_month, day=1)
                    current -= timedelta(days=1)
        else:
            current += step
    return dates


def calculate(prices):
    dates = sorted(prices.keys())
    latest_date = dates[-1]
    first_date = dates[0]

    latest = datetime.strptime(latest_date, '%Y-%m-%d').date()
    first = datetime.strptime(first_date, '%Y-%m-%d').date()

    chart_start = add_years(latest, -YEARS_AGO)
    if chart_start < first:
        chart_start = first

    accum_start = chart_start
    accum_end = add_years(chart_start, ACCUMULATE_YEARS)
    if accum_end > latest:
        accum_end = latest

    purchase_dates = get_purchase_dates(accum_start.isoformat(), accum_end.isoformat(), FREQUENCY)
    purchase_set = set(purchase_dates)

    total_invested = 0.0
    total_btc = 0.0
    history = []
    chart_data = []

    current = chart_start
    one_day = timedelta(days=1)
    one_week = timedelta(days=7)

    # Daily walk for accurate BTC accumulation and final value.
    while current <= latest:
        date_str = current.isoformat()
        day = prices.get(date_str)

        if day:
            if date_str in purchase_set:
                daily_high = day['h']
                if daily_high and daily_high > 0:
                    btc_bought = AMOUNT / daily_high
                    total_invested += AMOUNT
                    total_btc += btc_bought
                    history.append({
                        'date': date_str,
                        'price': daily_high,
                        'invested': AMOUNT,
                        'btcBought': btc_bought,
                        'runningBtc': total_btc,
                    })

            daily_low = day['l']
            value = total_btc * daily_low if daily_low and daily_low > 0 else 0.0

            # Sample chart data weekly (on purchase day cadence) and at the final date.
            if current == chart_start or (current - chart_start).days % 7 == 0 or current == latest:
                chart_data.append({
                    'date': date_str,
                    'value': value,
                    'invested': total_invested,
                })

        current += one_day

    # Ensure the very latest date is always included even if it doesn't fall on a weekly sample.
    if chart_data[-1]['date'] != latest_date:
        final_day = prices[latest_date]
        final_value = total_btc * final_day['l'] if final_day.get('l') else 0.0
        chart_data.append({
            'date': latest_date,
            'value': final_value,
            'invested': total_invested,
        })

    current_value = chart_data[-1]['value']
    profit_loss = current_value - total_invested
    roi = (profit_loss / total_invested) * 100 if total_invested > 0 else 0.0
    cagr = ((current_value / total_invested) ** (1 / YEARS_AGO) - 1) * 100 if total_invested > 0 and current_value > 0 else 0.0

    # Keep history compact: first 10, last 10, ellipsis in the middle.
    compact_history = history
    if len(history) > 20:
        compact_history = history[:10] + [{'date': '...'}] + history[-10:]

    # Store clean numeric types.
    total_invested_clean = int(total_invested) if total_invested == int(total_invested) else round(total_invested, 2)

    return {
        'amount': AMOUNT,
        'frequency': FREQUENCY,
        'yearsAgo': YEARS_AGO,
        'accumulateYears': ACCUMULATE_YEARS,
        'totalInvested': total_invested_clean,
        'totalBtc': total_btc,
        'currentValue': current_value,
        'profitLoss': profit_loss,
        'roi': roi,
        'cagr': cagr,
        'purchaseCount': len(history),
        'chartData': chart_data,
        'history': compact_history,
    }


def main():
    print('Loading prices...')
    prices = load_prices()
    print(f'Loaded {len(prices):,} price records')

    result = calculate(prices)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, separators=(',', ':'))

    print(f"✓ Wrote {OUTPUT_FILE}")
    print(f"  Total invested: ${result['totalInvested']:,.2f}")
    print(f"  Current value:  ${result['currentValue']:,.2f}")
    print(f"  ROI:            {result['roi']:,.2f}%")
    print(f"  CAGR:           {result['cagr']:,.2f}%")
    print(f"  Purchases:      {result['purchaseCount']}")


if __name__ == '__main__':
    main()
