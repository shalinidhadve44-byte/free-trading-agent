
import json
import urllib.request
from datetime import datetime, timezone


# Free prototype: public Binance market data.
# Research only — no orders, no API keys, no trading advice.

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = "15m"
CANDLE_LIMIT = 100


def fetch_candles(symbol):
    url = (
        "https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={INTERVAL}&limit={CANDLE_LIMIT}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FreeTradingResearchAgent/1.0"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        rows = json.loads(response.read().decode("utf-8"))

    # Ignore the last candle because it may still be forming.
    return [
        {
            "close": float(row[4]),
            "high": float(row[2]),
            "low": float(row[3]),
            "volume": float(row[5]),
        }
        for row in rows[:-1]
    ]


def ema(values, period):
    if len(values) < period:
        return None

    result = sum(values[:period]) / period
    multiplier = 2 / (period + 1)

    for value in values[period:]:
        result = (value * multiplier) + (result * (1 - multiplier))

    return result


def analyse(symbol):
    candles = fetch_candles(symbol)
    closes = [candle["close"] for candle in candles]

    if len(closes) < 60:
        return {"symbol": symbol, "status": "INSUFFICIENT DATA"}

    fast = ema(closes, 20)
    slow = ema(closes, 50)
    price = closes[-1]

    if fast is None or slow is None:
        return {"symbol": symbol, "status": "INSUFFICIENT DATA"}

    # These are research conditions, not validated trading signals.
    if price > slow and fast > slow:
        status = "BULLISH CONDITIONS — NOT A BUY RECOMMENDATION"
    elif price < slow and fast < slow:
        status = "BEARISH CONDITIONS — NOT A SELL RECOMMENDATION"
    else:
        status = "MIXED CONDITIONS — NO SETUP"

    return {
        "symbol": symbol,
        "interval": INTERVAL,
        "last_completed_close": price,
        "ema20": round(fast, 4),
        "ema50": round(slow, 4),
        "status": status,
    }


def main():
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "RESEARCH ONLY — NO LIVE TRADING",
        "results": [],
    }

    for symbol in SYMBOLS:
        try:
            report["results"].append(analyse(symbol))
        except Exception as error:
            report["results"].append({
                "symbol": symbol,
                "status": "DATA FETCH FAILED",
                "detail": str(error)[:200],
            })

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
