import asyncio
import os
import logging
import statistics
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import redis.asyncio as redis

# Enforce strict standard logging for centralized metric scraping
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("quant-consumer")

# Strict rolling window size
WINDOW_SIZE = 50
price_window = deque(maxlen=WINDOW_SIZE)

def compute_algorithmic_signal(prices: list[float]) -> str:
    """
    Computes strict statistical variance on the live data window.
    No mock increments or artificial data points.
    """
    if len(prices) < 2:
        return "HOLD (Insufficient window size for accurate variance)"
    
    variance = statistics.variance(prices)
    latest_price = prices[-1]
    median_price = statistics.median(prices)
    
    if variance > 50.0:
        if latest_price > median_price:
            return f"SELL (Variance: {variance:.4f} | Condition: Overbought relative to median)"
        else:
            return f"BUY (Variance: {variance:.4f} | Condition: Oversold relative to median)"
    
    return f"HOLD (Variance: {variance:.4f} | Condition: Low Volatility)"

async def consume_live_stream():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.fatal("REDIS_URL environment variable is strictly required.")
        exit(1)
        
    redis_client = redis.from_url(redis_url, decode_responses=True)
    stream_key = 'market:stream:live'
    last_id = '0-0'
    
    logger.info(f"Connected to Redis cluster. Initiating strict XREAD on {stream_key}")

    try:
        while True:
            # Execute ACTUAL blocking XREAD command
            events = await redis_client.xread({stream_key: last_id}, count=10, block=5000)
            
            if not events:
                continue
                
            for stream_name, messages in events:
                for message_id, data in messages:
                    last_id = message_id 
                    
                    if "price" in data:
                        actual_price = float(data["price"])
                        price_window.append(actual_price)
                        
                        signal = compute_algorithmic_signal(list(price_window))
                        logger.info(f"[Signal Engine] ID: {message_id} | Price: ${actual_price} | Execution: {signal}")
                        
    except asyncio.CancelledError:
        logger.info("Stream consumption task cancelled during shutdown.")
    except Exception as e:
        logger.error(f"[Fatal] Consumer process failure: {e}")
    finally:
        await redis_client.aclose()

# --- FastAPI Integration for Uvicorn & Docker Healthchecks ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background task when the server boots
    task = asyncio.create_task(consume_live_stream())
    yield
    # Gracefully cancel the background task when the server shuts down
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

# This resolves the `Attribute "app" not found` uvicorn error
app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """
    Required by Docker Compose / Kubernetes readiness probes to verify 
    the container is alive and processing data.
    """
    return {
        "status": "healthy",
        "service": "quant-consumer",
        "current_window_size": len(price_window)
    }