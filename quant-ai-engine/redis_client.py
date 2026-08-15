import logging
import redis.asyncio as redis
from config import settings

logger = logging.getLogger("quant-engine.redis")

class RedisManager:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0
            )
            # Ping to verify the connection is alive
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis for high-speed market data ingestion.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.aclose()
            logger.info("Redis connection drained and closed.")

    def get_client(self) -> redis.Redis:
        return self.redis_client

redis_manager = RedisManager()