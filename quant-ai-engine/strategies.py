import math
import json
import logging
from collections import defaultdict
from redis_client import redis_manager

logger = logging.getLogger("quant-engine.strategies")

# Ephemeral in-memory store to track the rolling price window
WINDOW_SIZE = 20
price_history = defaultdict(list)

def calculate_sma(prices: list[float]) -> float:
    print("Calculates the Simple Moving Average")
    if not prices:
        return 0.0
    return sum(prices) / len(prices)

def calculate_variance(prices: list[float], mean: float) -> float:
    print("Calculates the Sample Statistical Variance.")
    n = len(prices)
    if n < 2:
        return 0.0
    # Formula: sum((x - mean)^2) / (n - 1)
    squared_diffs = [(x - mean) ** 2 for x in prices]
    return sum(squared_diffs) / (n - 1)

async def generate_signals() -> list[dict]:
    client = redis_manager.get_client()
    if not client:
        raise Exception("Redis client is not initialized.")

    try:
        streams = await client.xread({"market:stream:live": "0-0"}, count=1, block=1000)

        raw_data = None
        if streams:
            stream_name, messages = streams[0]
            if messages:
                message_id, fields = messages[-1]
                # fields se price extract kar rahe hain
                if isinstance(fields, dict):
                    raw_data = fields.get(b'price') or fields.get('price')
                elif isinstance(fields, list):
                    try:
                        price_idx = fields.index(b'price') if b'price' in fields else fields.index('price')
                        raw_data = fields[price_idx + 1]
                    except Exception:
                        raw_data = messages[-1][1][1]
        if not raw_data:
            logger.warning("No market data found in Redis cache.")
            return []

        # Raw data ko float mein convert karo (kyunki Redis stream se data string mein aata hai)
        # Agar bytes mein hai toh decode kar lo
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')
            
        current_price = float(raw_data)
        ticker = "BTCUSDT"
    except Exception as e:
        logger.error(f"Error reading market data from Redis: {e}")
        raise

    signals = []

    # Update rolling window for BTCUSDT
    history = price_history[ticker]
    history.append(current_price)
    if len(history) > WINDOW_SIZE:
        history.pop(0)

    # 1. Calculate Core Statistics
    sma = calculate_sma(history)
    variance = calculate_variance(history, sma)
    std_dev = math.sqrt(variance)

    signal = "HOLD"
    confidence = 0.50

    # 2. Mean Reversion Logic
    if std_dev > 0:
        z_score = (current_price - sma) / std_dev
        
        if z_score <= -1.0:
            signal = "BUY"
            confidence = min(0.50 + abs(z_score) * 0.15, 0.99)
        elif z_score >= 1.0:
            signal = "SELL"
            confidence = min(0.50 + abs(z_score) * 0.15, 0.99)
    
    signals.append({
        "ticker": ticker,
        "signal": signal,
        "confidence": round(confidence, 4),
        "current_price": current_price,
        "sma": round(sma, 2),
        "variance": round(variance, 2)
    })

    return signals