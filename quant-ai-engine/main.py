import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import traceback

from config import settings
from redis_client import redis_manager
from strategies import generate_signals

# Standardized JSON/Text logging format for production observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("quant-engine.main")

# Background Event-Driven Worker Loop
async def background_signal_processor():
    logger.info("Background Quant Worker started. Processing strategy signals...")
    
    while True:
        try:
            # Generate signals from the existing strategy
            signals = await generate_signals()
            
            if signals:
                redis_client = getattr(redis_manager, "client", None) or getattr(redis_manager, "redis", None) or redis_manager
                if not hasattr(redis_client, "xadd") and hasattr(redis_manager, "redis_client"):
                    redis_client = redis_manager.redis_client

                for sig in signals:
                    # Strictly cast EVERY value to string so Redis never sees a 'NoneType'
                    payload = {
                        "action": str(sig.get("action", "UNKNOWN")),
                        "symbol": str(sig.get("symbol", "BTCUSDT")),
                        "price": str(sig.get("price", 0.0)),
                        "z_score": str(sig.get("z_score", 0.0))
                    }
                    
                    await redis_client.xadd("market:stream:signals", payload)
                    logger.info(f"Signal pushed to market:stream:signals -> {payload}")
            
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            logger.info("Background signal processor cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in background signal processor: {e}")
            # This will print the exact line number if anything fails again
            logger.error(traceback.format_exc())
            await asyncio.sleep(2)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Quant AI Engine...")
    worker_task = None
    try:
        await redis_manager.connect()
        # Start background event-driven loop on startup
        worker_task = asyncio.create_task(background_signal_processor())
    except Exception as e:
        logger.error(f"Critical startup failure: {e}")
    
    yield  # Application is running
    
    logger.info("Received termination signal. Shutting down gracefully...")
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
    await redis_manager.disconnect()

# Initialize FastAPI
app = FastAPI(
    title="Quant AI Engine",
    description="Algorithmic Trading & Statistical Analysis Engine",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {
        "status": "operational", 
        "service": "quant-ai-engine"
    }

# Bind to the path explicitly proxied by the API Gateway
@app.get("/api/quant/signal")
async def get_trading_signals():
    try:
        signals = await generate_signals()
        
        if not signals:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "Service Unavailable",
                    "message": "Market data stream is currently unavailable in the Redis cache."
                }
            )
            
        return {
            "success": True,
            "data": signals
        }
        
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error during quantitative analysis pipeline."
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=False
    )