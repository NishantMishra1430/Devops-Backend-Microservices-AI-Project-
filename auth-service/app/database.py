import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

logger = logging.getLogger("auth-service")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.fatal("DATABASE_URL environment variable is missing.")
    exit(1)

# Initialize async engine for high-throughput Postgres connections
engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session