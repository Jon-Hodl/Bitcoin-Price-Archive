# 📈📉 The Bitcoin Price Archive

![Bitcoin Price Archive Banner](banner.png)

A free, public API for historical Bitcoin price data. Updated daily from mempool.space.

## Quick Start

### Get All Prices
```bash
curl https://jon-hodl.github.io/Bitcoin-Price/prices.json
```

### JavaScript Fetch
```javascript
const response = await fetch('https://jon-hodl.github.io/Bitcoin-Price/prices.json');
const prices = await response.json();

// Access specific date
const july15 = prices['2024-07-15'];
console.log(july15); // { o: 62000, h: 65000, l: 61000, c: 63000 }
```

## Data Format

Each date contains OHLC (Open, High, Low, Close) prices in USD:

```json
{
  "2024-07-15": {
    "o": 62000,  // Open
    "h": 65000,  // High
    "l": 61000,  // Low
    "c": 63000   // Close
  }
}
```

## Data Coverage

- **Start Date**: 2009-07-11 (early Bitcoin trading)
- **End Date**: Present day (updated daily)
- **Frequency**: Daily
- **Source**: mempool.space API

## Usage Examples

### Calculate Volatility
```javascript
const day = prices['2024-07-15'];
const volatility = day.h - day.l;
const volatilityPct = (volatility / day.l) * 100;
console.log(`Daily volatility: $${volatility} (${volatilityPct.toFixed(1)}%)`);
```

### Get Price on Specific Date
```javascript
function getPrice(dateString) {
  return prices[dateString]?.c || null; // Returns close price
}

const price = getPrice('2024-01-01');
```

### Calculate Average Price for Month
```javascript
function getMonthlyAverage(year, month) {
  const prefix = `${year}-${String(month).padStart(2, '0')}`;
  const monthPrices = Object.entries(prices)
    .filter(([date]) => date.startsWith(prefix))
    .map(([, data]) => data.c);
  
  if (monthPrices.length === 0) return null;
  
  const sum = monthPrices.reduce((a, b) => a + b, 0);
  return sum / monthPrices.length;
}
```

## CORS

This API is CORS-enabled via GitHub Pages. Use it from any website:

```html
<script>
fetch('https://jon-hodl.github.io/Bitcoin-Price/prices.json')
  .then(r => r.json())
  .then(prices => console.log('Loaded', Object.keys(prices).length, 'days of data'));
</script>
```

## Projects Using This API

- [Bitcoin Time Machine](https://github.com/Jon-Hodl/bitcoin-time-machine) - Transaction analysis tool

## Rate Limits

No rate limits! This is a static JSON file served via GitHub Pages CDN. Cache as needed.

## License

MIT - Free for any use

## Contributing

This database is auto-updated daily. To report issues or request features, open an issue.
