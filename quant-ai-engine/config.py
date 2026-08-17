import logging
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PORT: int = 3002
    HOST: str = "0.0.0.0"
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    logging.basicConfig(level=logging.FATAL)
    logging.fatal(f"Quant AI Engine Config Error: Missing or invalid environment variables.{e}")
    sys.exit(1)