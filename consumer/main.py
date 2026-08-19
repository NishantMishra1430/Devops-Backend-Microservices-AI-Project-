import asyncio
import os
import logging
import statistics
import json
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

# Enforce strict standard logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("quant-consumer")

# Strict rolling window size
WINDOW_SIZE = 50
price_window = deque(maxlen=WINDOW_SIZE)

def compute_algorithmic_signal(prices: list[float]) -> dict:
    """
    Computes strict statistical variance and returns a structured dictionary
    so the data can be cleanly serialized to JSON for the Execution Engine.
    """
    if len(prices) < 2:
        return {"action": "HOLD", "variance": 0.0, "condition": "Insufficient window size"}
    
    variance = statistics.variance(prices)
    latest_price = prices[-1]
    median_price = statistics.median(prices)
    
    # Note: 50.0 is used as a strict operational threshold for BTC volatility
    if variance > 50.0:
        if latest_price > median_price:
            return {"action": "SELL", "variance": variance, "condition": "Overbought relative to median"}
        else:
            return {"action": "BUY", "variance": variance, "condition": "Oversold relative to median"}
    
    return {"action": "HOLD", "variance": variance, "condition": "Low Volatility"}

async def consume_live_stream():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.fatal("REDIS_URL environment variable is strictly required.")
        exit(1)
        
    redis_client = redis.from_url(redis_url, decode_responses=True)
    stream_key_in = 'market:stream:live'
    stream_key_out = 'market:stream:signals'
    last_id = '0-0'
    
    logger.info(f"Connected to Redis. Listening on {stream_key_in} | Publishing to {stream_key_out}")

    try:
        while True:
            # Execute ACTUAL blocking XREAD command
            events = await redis_client.xread({stream_key_in: last_id}, count=10, block=5000)
            
            if not events:
                continue
                
            for stream_name, messages in events:
                for message_id, data in messages:
                    last_id = message_id 
                    
                    if "price" in data:
                        actual_price = float(data["price"])
                        price_window.append(actual_price)
                        
                        # Get structured signal data
                        signal_data = compute_algorithmic_signal(list(price_window))
                        action = signal_data["action"]
                        
                        logger.info(f"[Signal Engine] ID: {message_id} | Price: ${actual_price} | Execution: {action}")
                        
                        # Hand-off: Only publish actionable signals to the Execution Engine
                        if action in ["BUY", "SELL"]:
                            payload = {
                                "symbol": "BTCUSDT",
                                "signal": action,
                                "price": actual_price,
                                "variance": signal_data["variance"],
                                "condition": signal_data["condition"]
                            }
                            
                            # Execute ACTUAL XADD to the signals stream. Cap the stream at 1000 items.
                            await redis_client.xadd(
                                stream_key_out, 
                                {"payload": json.dumps(payload)}, 
                                maxlen=1000
                            )
                            logger.info(f"[Publisher] Successfully routed {action} signal to {stream_key_out}")
                        
    except asyncio.CancelledError:
        logger.info("Stream consumption task cancelled during shutdown.")
    except Exception as e:
        logger.error(f"[Fatal] Consumer process failure: {e}")
    finally:
        await redis_client.aclose()

# --- FastAPI Integration for Uvicorn & Docker Healthchecks ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(consume_live_stream())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "quant-consumer",
        "current_window_size": len(price_window)
    }