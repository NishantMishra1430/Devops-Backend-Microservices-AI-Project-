import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from redis_client import redis_manager
from strategies import generate_signals

# Standardized JSON/Text logging format for production observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("quant-engine.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Quant AI Engine...")
    try:
        await redis_manager.connect()
    except Exception as e:
        logger.error(f"Critical startup failure: {e}")
        # Allow Fastapi to boot so orchestration tools can poll health checks and see the failure
    
    yield  # Application is running
    
    logger.info("Received termination signal. Shutting down gracefully...")
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
    # Bypassed if executed via Docker/Gunicorn in production, but useful for local execution
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=False
    )