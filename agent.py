
import json
import urllib.request
from datetime import datetime, timezone

# Free research prototype using Kraken public market data.
# Research only — no orders, no API keys, no trading advice.

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = 15
CANDLE_LIMIT = 100


def fetch_candles(symbol):
    pairs = {
        "BTCUSDT": "XBTUSD",
        "ETHUSDT": "ETHUSD",
    }

    pair = pairs.get(symbol)
    if pair is None:
        raise ValueError(f"Unsupported symbol: {symbol}")

    url = (
        "https://api.kraken.com/0/public/OHLC"
        f"?pair={pair}&interval={INTERVAL}"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FreeTradingResearchAgent/1.0"},
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("error"):
        raise ValueError("; ".join(payload["error"]))

    result = payload["result"]
    pair_key = next(key for key in result if key != "last")
    rows = result[pair_key]

    # Exclude the current, potentially incomplete candle.
    rows = rows[:-1][-CANDLE_LIMIT:]

    return [
        {
            "close": float(row[4]),
            "high": float(row[2]),
            "low": float(row[3]),
            "volume": float(row[6]),
        }
        for row in rows
    ]


def ema(values, period):
    if len(values) < period:
        return None

    result = sum(values[:period]) / period
    multiplier = 2 / (period + 1)

    for value in values[period:]:
        result = (value * multiplier) + (
            result * (1 - multiplier)
        )

    return result


def analyse(symbol):
    candles = fetch_candles(symbol)
    closes = [candle["close"] for candle in candles]

    if len(closes) < 60:
        return {
            "symbol": symbol,
            "status": "INSUFFICIENT DATA",
            "candles_received": len(closes),
        }

    fast = ema(closes, 20)
    slow = ema(closes, 50)
    price = closes[-1]

    if price > slow and fast > slow:
        status = "BULLISH CONDITIONS — NOT A BUY RECOMMENDATION"
    elif price < slow and fast < slow:
        status = "BEARISH CONDITIONS — NOT A SELL RECOMMENDATION"
    else:
        status = "MIXED CONDITIONS — NO SETUP"

    return {
        "symbol": symbol,
        "interval": f"{INTERVAL}m",
        "last_completed_close": price,
        "ema20": round(fast, 4),
        "ema50": round(slow, 4),
        "status": status,
    }


def main():
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "RESEARCH ONLY — NO LIVE TRADING",
        "data_source": "Kraken public OHLC API",
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
