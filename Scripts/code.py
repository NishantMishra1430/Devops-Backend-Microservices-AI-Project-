from pathlib import Path


def api_gateway():
    api = Path("api-gateway")
    main = Path("api-gateway/src")
    server_file = main / "server.js"
    config = main / "config"
    plugins = main / "plugins"
    env_file = config / "env.js"
    proxy_file = plugins / "proxy.js"

    main.mkdir(parents=True, exist_ok=True)

    env_content = """import { z } from 'zod';
import 'dotenv/config';

const envSchema = z.object({
  PORT: z.string().default('3000'),
  HOST: z.string().default('0.0.0.0'),
  MARKET_DATA_URL: z.string().url('MARKET_DATA_URL must be a valid URL'),
  QUANT_ENGINE_URL: z.string().url('QUANT_ENGINE_URL must be a valid URL'),
  EXECUTION_SERVICE_URL: z.string().url('EXECUTION_SERVICE_URL must be a valid URL')
});

const parseResult = envSchema.safeParse(process.env);

if (!parseResult.success) {
  console.error(
    JSON.stringify({
      level: 'fatal',
      time: new Date().toISOString(),
      msg: 'API Gateway Environment Validation Error',
      errors: parseResult.error.format()
    })
  );
  process.exit(1);
}

export const env = parseResult.data;
"""

    proxy_content = """import httpProxy from '@fastify/http-proxy';
import fp from 'fastify-plugin';
import { env } from '../config/env.js';

async function proxyPlugin(fastify, options) {
  // 1. Proxy -> Market Data Ingestor
  await fastify.register(httpProxy, {
    upstream: env.MARKET_DATA_URL,
    prefix: '/api/market',
    replyOptions: {
      onError: (reply, error) => {
        fastify.log.error(`Market Data Proxy Error: ${error.message}`);
        reply.code(502).send({
          statusCode: 502,
          error: 'Bad Gateway',
          message: 'Market Data Service is temporarily unavailable.'
        });
      }
    }
  });

  // 2. Proxy -> Quant AI Engine (Python FastAPI)
  await fastify.register(httpProxy, {
    upstream: env.QUANT_ENGINE_URL,
    prefix: '/api/quant',
    replyOptions: {
      onError: (reply, error) => {
        fastify.log.error(`Quant AI Engine Proxy Error: ${error.message}`);
        reply.code(502).send({
          statusCode: 502,
          error: 'Bad Gateway',
          message: 'Quant AI Engine is temporarily unavailable.'
        });
      }
    }
  });

  // 3. Proxy -> Execution Engine
  await fastify.register(httpProxy, {
    upstream: env.EXECUTION_SERVICE_URL,
    prefix: '/api/execute',
    replyOptions: {
      onError: (reply, error) => {
        fastify.log.error(`Execution Service Proxy Error: ${error.message}`);
        reply.code(502).send({
          statusCode: 502,
          error: 'Bad Gateway',
          message: 'Execution Engine is temporarily unavailable.'
        });
      }
    }
  });
}

export default fp(proxyPlugin);
"""

    server_content = """import fastify from 'fastify';
import { env } from './config/env.js';
import proxyPlugin from './plugins/proxy.js';

// Initialize Fastify with highly optimized built-in Pino logger
const app = fastify({
  logger: {
    level: 'info',
    timestamp: () => `,"time":"${new Date().toISOString()}"`
  }
});

// Centralized Error Handling
app.setErrorHandler((error, request, reply) => {
  app.log.error({ err: error, requestPath: request.url }, 'Global Error Handler Triggered');
  reply.status(error.statusCode || 500).send({
    statusCode: error.statusCode || 500,
    error: error.name || 'Internal Server Error',
    message: error.message || 'An unexpected error occurred in the API Gateway'
  });
});

// Infrastructure Health Check
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'api-gateway', 
    timestamp: new Date().toISOString() 
  };
});

// Mount the microservice proxy routes
app.register(proxyPlugin);

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 QuantTrade API Gateway active at http://${env.HOST}:${env.PORT}`);

    const shutdown = async (signal) => {
      app.log.info(`\\nReceived ${signal}, initiating graceful shutdown...`);
      await app.close();
      app.log.info('API Gateway closed successfully. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'API Gateway failed to initialize');
    process.exit(1);
  }
};

startServer();
"""

    if not config.exists():
        config.mkdir(parents=True)
        print(f"{config} folder Created inside {main}...")
    else:
        print(f"{config} folder is already present...")

    if not env_file.exists():
        env_file.touch()
        print(f"{env_file} file Created inside {config} Folder...")
        print(f"Code Inserting...")
        env_file.write_text(env_content)
        print(f"Successfully Created {env_file}...✅")
    else:
        print(f"{env_file} file Already Exists in {config} folder...")

    if not plugins.exists():
        plugins.mkdir(parents=True)
        print(f"{plugins} folder Created inside {main}...")
    else:
        print(f"{plugins} folder is already present...")

    if not proxy_file.exists():
        proxy_file.touch()
        print(f"{proxy_file} file Created inside {plugins} Folder...")
        print(f"Code Inserting...")
        proxy_file.write_text(proxy_content)
        print(f"Successfully Created {proxy_file}...✅")
    else:
        print(f"{proxy_file} file Already Exists in {plugins} folder...")

    if not server_file.exists():
        server_file.touch()
        print(f"{server_file} file created inside {main} folder...")
        print(f"Code Inserting...")
        server_file.write_text(server_content)
        print(f"Successfully Created {server_file}...")
    else:
        print(f"{server_file} already exists...🎉")

    print("Task Successfully Completed...🎉✅🥂")


def market_data_service():
    main = Path("market-data-service")
    src = main / "src"  # done
    package = main / "package.json"  # done
    env = main / ".env"  # done
    config = src / "config"  # done
    env_js = config / "env.js"  # done
    services = src / "services"  # done
    redis_js = services / "redis.js"  # done
    marketMock_js = services / "marketMock.js"
    routes = src / "routes"  # done
    prices_js = routes / "prices.js"  # done
    server_js = src / "server.js"  # done

    package_content = """{
  "name": "market-data-service",
  "version": "1.0.0",
  "description": "Market Data Ingestor for QuantTrade Engine",
  "type": "module",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "node --watch src/server.js"
  },
  "dependencies": {
    "dotenv": "^16.4.5",
    "fastify": "^4.26.2",
    "ioredis": "^5.3.2",
    "zod": "^3.23.8"
  },
  "author": "",
  "license": "MIT"
}
    """

    env_content = """# Server Configuration
PORT=3001
HOST=0.0.0.0

# Redis Cache Connection
# Format: redis://username:password@host:port
REDIS_URL=redis://localhost:6379
    """

    env_js_content = """import { z } from 'zod';
import 'dotenv/config';

const envSchema = z.object({
  PORT: z.string().default('3001'),
  HOST: z.string().default('0.0.0.0'),
  REDIS_URL: z.string().url('REDIS_URL must be a valid Redis connection string')
});

const parseResult = envSchema.safeParse(process.env);

if (!parseResult.success) {
  console.error(
    JSON.stringify({
      level: 'fatal',
      time: new Date().toISOString(),
      msg: 'Market Data Service Environment Validation Error',
      errors: parseResult.error.format()
    })
  );
  process.exit(1);
}

export const env = parseResult.data;
    """

    redis_content = """import Redis from 'ioredis';
import { env } from '../config/env.js';

export const redis = new Redis(env.REDIS_URL, {
  maxRetriesPerRequest: 3,
  retryStrategy(times) {
    // Exponential backoff strategy
    return Math.min(times * 50, 2000);
  }
});

redis.on('error', (err) => {
  console.error(
    JSON.stringify({
      level: 'error',
      time: new Date().toISOString(),
      msg: 'Redis connection error',
      error: err.message
    })
  );
});

export const closeRedis = async () => {
  try {
    await redis.quit();
  } catch (error) {
    console.error('Error closing Redis connection', error);
  }
};
    """

    marketmock_content = """import { redis } from './redis.js';

// Base state for our simulated market
const currentPrices = {
  BTC: 65000.00,
  ETH: 3500.00,
  AAPL: 175.50,
  TSLA: 210.20,
  SPY: 510.00
};

/**
 * Applies a random walk algorithm to simulate live market movements.
 * Caches the result in Redis for 2 seconds.
 */
export const getMarketPrices = async () => {
  const cacheKey = 'market:prices:latest';

  // 1. Check Redis for a cached, unexpired price tick
  const cachedPrices = await redis.get(cacheKey);
  if (cachedPrices) {
    return JSON.parse(cachedPrices);
  }

  // 2. Cache expired or empty. Calculate new prices (Tick)
  for (const ticker in currentPrices) {
    // Simulate a random market movement between -0.3% and +0.3%
    const volatility = 0.003; 
    const changePercentage = 1 + (Math.random() * volatility * 2 - volatility);
    
    currentPrices[ticker] = parseFloat((currentPrices[ticker] * changePercentage).toFixed(2));
  }

  // 3. Store in Redis with an EX (Expiration) of 2 seconds
  await redis.set(cacheKey, JSON.stringify(currentPrices), 'EX', 2);

  return currentPrices;
};"""

    price_content = """import { getMarketPrices } from '../services/marketMock.js';

export default async function priceRoutes(fastify, options) {
  
  const marketDataHandler = async (request, reply) => {
    try {
      const prices = await getMarketPrices();
      
      return reply.code(200).send({
        success: true,
        timestamp: new Date().toISOString(),
        data: prices
      });
    } catch (error) {
      fastify.log.error(`Failed to fetch market prices: ${error.message}`);
      return reply.code(500).send({
        success: false,
        error: 'Internal Server Error',
        message: 'Unable to retrieve live market data'
      });
    }
  };

  // Bind to root (if gateway strips prefix)
  fastify.get('/', marketDataHandler);
  
  // Bind to specific path (if gateway passes raw URI)
  fastify.get('/api/market', marketDataHandler);
}
    """

    server_content = """import fastify from 'fastify';
import { env } from './config/env.js';
import { closeRedis } from './services/redis.js';
import priceRoutes from './routes/prices.js';

const app = fastify({
  logger: {
    level: 'info',
    timestamp: () => `,"time":"${new Date().toISOString()}"`
  }
});

// Centralized Error Handling
app.setErrorHandler((error, request, reply) => {
  app.log.error({ err: error, requestPath: request.url }, 'Global Error Handler');
  reply.status(error.statusCode || 500).send({
    success: false,
    statusCode: error.statusCode || 500,
    error: error.name || 'Internal Server Error',
    message: 'An unexpected error occurred in the Market Data Service'
  });
});

// Infrastructure Health Check
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'market-data-service', 
    timestamp: new Date().toISOString() 
  };
});

// Register Market Routes
app.register(priceRoutes);

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 Market Data Service active at http://${env.HOST}:${env.PORT}`);

    // SIGINT (Ctrl+C) & SIGTERM (Docker/K8s kill signal) Handling
    const shutdown = async (signal) => {
      app.log.info(`\nReceived ${signal}, initiating graceful shutdown...`);
      
      // 1. Stop accepting new HTTP requests
      await app.close();
      app.log.info('HTTP server closed.');
      
      // 2. Drain and close Redis connections
      await closeRedis();
      app.log.info('Redis connection successfully closed.');
      
      app.log.info('Market Data Service shutdown complete. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'Market Data Service failed to initialize');
    process.exit(1);
  }
};

startServer();"""

    src.mkdir(exist_ok=True, parents=True)

    if not config.exists():
        config.mkdir(parents=True)
        print(f"Created a {config} folder inside {src} folder")
    else:
        print(f"{config} folder already present...")

    if not services.exists():
        services.mkdir(parents=True)
        print(f"Created a {services} folder inside {src} folder")
    else:
        print(f"{services} folder already present...")

    if not routes.exists():
        routes.mkdir(parents=True)
        print(f"Created a {routes} folder inside {src} folder")
    else:
        print(f"{routes} folder already present...")

    if not package.exists():
        package.touch()
        package.write_text(package_content)
    else:
        print(f"{package} file already presented...")

    if not env.exists():
        env.touch()
        env.write_text(env_content)
    else:
        print(f"{env} file already presented...")

    if not env_js.exists():
        env_js.touch()
        env_js.write_text(env_js_content)
    else:
        print(f"{env_js} file already presented...")

    if not redis_js.exists():
        redis_js.touch()
        redis_js.write_text(redis_content)
    else:
        print(f"{redis_js} file is already presented...")

    if not marketMock_js.exists():
        marketMock_js.touch()
        marketMock_js.write_text(marketmock_content)
    else:
        print(f"{marketMock_js} file is already presented...")

    if not prices_js.exists():
        prices_js.touch()
        prices_js.write_text(price_content)
    else:
        print(f"{prices_js} file is already presented...")

    if not server_js.exists():
        server_js.touch()
        server_js.write_text(server_content)
    else:
        print(f"{server_js} file is already presented...")

    print("Task Automated successfully....✅🎉🥂🤖")


def quant_ai_engine():
    main = Path("quant-ai-engine")
    requirement = main / "requirements.txt"
    env = main / ".env"
    config = main / "config.py"
    redis_client = main / "redis_client.py"
    strategies = main / "strategies.py"
    main_py = main / "main.py"
    
    main.mkdir(parents=True, exist_ok=True)
    print(f"{main} folder created/verified...")

    requirement_content = """fastapi==0.111.0
uvicorn==0.29.0
pydantic==2.7.1
pydantic-settings==2.2.1
redis==5.0.4"""
    env_content = """# Server Configuration
PORT=3002
HOST=0.0.0.0

# Redis Cache Connection
# Format: redis://username:password@host:port
REDIS_URL=redis://localhost:6379"""
    config_content = """import logging
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
    logging.fatal(f"Quant AI Engine Config Error: Missing or invalid environment variables.\n{e}")
    sys.exit(1)"""
    redis_client_content = """import logging
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

redis_manager = RedisManager()"""
    strategies_content = """import math
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
        raw_data = await client.get("market:prices:latest")
        if not raw_data:
            logger.warning("No market data found in Redis cache.")
            return []

        current_prices = json.loads(raw_data)
    except Exception as e:
        logger.error(f"Error reading market data from Redis: {e}")
        raise

    signals = []

    for ticker, current_price in current_prices.items():
        # Update rolling window
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
            # Calculate Z-Score (Standard scores away from the mean)
            z_score = (current_price - sma) / std_dev
            
            # If price drops more than 1 standard deviation below SMA, it is oversold -> BUY
            if z_score <= -1.0:
                signal = "BUY"
                confidence = min(0.50 + abs(z_score) * 0.15, 0.99)
            
            # If price spikes more than 1 standard deviation above SMA, it is overbought -> SELL
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

    return signals"""
    main_content = """import logging
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
    )"""
    
    if not requirement.exists():
      requirement.touch()
      print(f"Creating {requirement} file inside {main} folder...")
      requirement.write_text(requirement_content)
    else:
      print(f"{requirement} file already exists...")
    
    if not env.exists():
          env.touch()
          print(f"Creating {requirement} file inside {main} folder...")
          env.write_text(env_content)
    else:
      print(f"{env} file already exists...")
      
    if not config.exists():
          config.touch()
          print(f"Creating {config} file inside {main} folder...")
          config.write_text(config_content)
    else:
      print(f"{config} file already exists...")

    if not redis_client.exists():
          redis_client.touch()
          print(f"Creating {redis_client} file inside {main} folder...")
          redis_client.write_text(redis_client_content)
    else:
      print(f"{redis_client} file already exists...")
      
    if not strategies.exists():
          strategies.touch()
          print(f"Creating {strategies} file inside {main} folder...")
          strategies.write_text(strategies_content)
    else:
      print(f"{strategies} file already exists...")
      
    if not main_py.exists():
          main_py.touch()
          print(f"Creating {main_py} file inside {main} folder...")
          main_py.write_text(main_content)
    else:
      print(f"{main_py} file already exists...")
      
    print("Task Automated Successfully...🥂🎉✅")

def execution_service():
    main = Path("execution-service")
    package = main / "package.json" # done 
    env = main / ".env" # done 
    src = main / "src" # done 
    config = src / "config" # done 
    env_js = config / "env.js" # done 
    services = src / "services" # done 
    db_js = services / "db.js" # done
    rabbitmq = services / "rabbitmq.js" # done 
    routes = src / "routes" # done
    trade_js = routes / "trade.js" # done
    server = src / "server.js" # done 
    if not src.exists():
        print(f"Creating {src} folder inside the {main} folder...")
        src.mkdir(parents=True)
    else:
        print(f"{src} folder already exists...")

    if not config.exists():
        print(f"Creating {config} folder inside the {src} folder...")
        config.mkdir(parents=True)
    else:
        print(f"{config} folder already exists...")

    if not services.exists():
        print(f"Creating {services} folder inside the {src} folder...")
        services.mkdir(parents=True)
    else:
        print(f"{services} folder already exists...")

    if not routes.exists():
        print(f"Creating {routes} folder inside the {src} folder...")
        routes.mkdir(parents=True)
    else:
        print(f"{routes} folder already exists...")

    package_content = """{
  "name": "execution-service",
  "version": "1.0.0",
  "description": "Trade Execution Service for QuantTrade Engine",
  "type": "module",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "node --watch src/server.js"
  },
  "dependencies": {
    "amqplib": "^0.10.4",
    "axios": "^1.6.8",
    "dotenv": "^16.4.5",
    "fastify": "^4.26.2",
    "pg": "^8.11.5",
    "zod": "^3.23.8"
  },
  "author": "",
  "license": "MIT"
}"""
    env_content = """# Server Configuration
PORT=3003
HOST=0.0.0.0

# Database Configuration
# Format: postgresql://username:password@host:port/database
DB_URL=postgresql://postgres:password@localhost:5432/quanttrade

# RabbitMQ Broker Configuration
# Format: amqp://username:password@host:port
RABBITMQ_URL=amqp://localhost:5672

# Upstream Services
QUANT_ENGINE_URL=http://localhost:3002"""
    env_js_content = """import { z } from 'zod';
import 'dotenv/config';

const envSchema = z.object({
  PORT: z.string().default('3003'),
  HOST: z.string().default('0.0.0.0'),
  DB_URL: z.string().url('DB_URL must be a valid PostgreSQL connection string'),
  RABBITMQ_URL: z.string().url('RABBITMQ_URL must be a valid AMQP connection string'),
  QUANT_ENGINE_URL: z.string().url('QUANT_ENGINE_URL must be a valid URL')
});

const parseResult = envSchema.safeParse(process.env);

if (!parseResult.success) {
  console.error(
    JSON.stringify({
      level: 'fatal',
      time: new Date().toISOString(),
      msg: 'Execution Service Environment Validation Error',
      errors: parseResult.error.format()
    })
  );
  process.exit(1);
}

export const env = parseResult.data;"""
    db_js_content = """import pg from 'pg';
import { env } from '../config/env.js';

export const pool = new pg.Pool({
  connectionString: env.DB_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  console.error(
    JSON.stringify({
      level: 'error',
      time: new Date().toISOString(),
      msg: 'Unexpected error on idle PostgreSQL client',
      error: err.message
    })
  );
});

export const initDb = async (logger) => {
  let retries = 5;
  while (retries > 0) {
    try {
      const client = await pool.connect();
      await client.query(`
        CREATE TABLE IF NOT EXISTS trades (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          ticker VARCHAR(10) NOT NULL,
          action VARCHAR(10) NOT NULL,
          amount_usd DECIMAL(12, 2) NOT NULL,
          price DECIMAL(12, 2) NOT NULL,
          timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
      `);
      client.release();
      logger.info('PostgreSQL initialized: trades table verified.');
      return;
    } catch (error) {
      retries -= 1;
      logger.warn(`PostgreSQL not ready, retrying... (${retries} attempts left)`);
      if (retries === 0) {
        logger.error(`Failed to connect to PostgreSQL: ${error.message}`);
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
};

export const closeDb = async () => {
  try {
    await pool.end();
  } catch (error) {
    console.error('Error closing PostgreSQL pool', error);
  }
};"""
    rabbitmq_content = """import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';

export const initRabbitMQ = async (logger) => {
  let retries = 5;
  while (retries > 0) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();
      
      // Ensure the queue exists before we try to publish to it
      await channel.assertQueue(QUEUE_NAME, { durable: true });
      
      logger.info('RabbitMQ initialized: connection established and queue verified.');
      
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
      });
      
      return;
    } catch (error) {
      retries -= 1;
      logger.warn(`RabbitMQ not ready, retrying... (${retries} attempts left)`);
      if (retries === 0) {
        logger.error(`Failed to connect to RabbitMQ: ${error.message}`);
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
};

export const publishTradeEvent = async (tradePayload, logger) => {
  if (!channel) {
    throw new Error('RabbitMQ channel is not initialized');
  }
  
  const message = Buffer.from(JSON.stringify(tradePayload));
  const published = channel.sendToQueue(QUEUE_NAME, message, {
    persistent: true,
    messageId: tradePayload.id 
  });
  
  if (published) {
    logger.info({ tradeId: tradePayload.id }, 'Trade event published to RabbitMQ successfully.');
  } else {
    logger.error({ tradeId: tradePayload.id }, 'RabbitMQ buffer full, failed to publish trade event.');
  }
};

export const closeRabbitMQ = async () => {
  try {
    if (channel) await channel.close();
    if (connection) await connection.close();
  } catch (error) {
    console.error('Error closing RabbitMQ connection', error);
  }
};"""

    trade_js_content = """import axios from 'axios';
import { env } from '../config/env.js';
import { pool } from '../services/db.js';
import { publishTradeEvent } from '../services/rabbitmq.js';

export default async function tradeRoutes(fastify, options) {
  
  fastify.post('/api/execute/trade', async (request, reply) => {
    const { ticker, amount_usd } = request.body;

    if (!ticker || !amount_usd || typeof amount_usd !== 'number') {
      return reply.code(400).send({
        success: false,
        error: 'Bad Request',
        message: 'Payload must include a valid ticker (string) and amount_usd (number).'
      });
    }

    try {
      // 1. Fetch live signals from Quant AI Engine
      const quantResponse = await axios.get(`${env.QUANT_ENGINE_URL}/api/quant/signal`);
      const signals = quantResponse.data?.data || [];
      
      // 2. Locate the specific ticker's signal
      const targetSignal = signals.find(s => s.ticker === ticker.toUpperCase());
      
      if (!targetSignal) {
        return reply.code(404).send({
          success: false,
          error: 'Not Found',
          message: `No active algorithmic signal found for ticker: ${ticker}`
        });
      }

      const { signal, current_price, confidence } = targetSignal;

      // 3. Process HOLD logic
      if (signal === 'HOLD') {
        fastify.log.info(`No execution for ${ticker} - Signal is HOLD.`);
        return reply.code(200).send({
          success: true,
          message: 'No trade executed. Algorithmic signal is HOLD.',
          data: { ticker, signal, current_price, confidence }
        });
      }

      // 4. Execute BUY/SELL: Insert into PostgreSQL
      const query = `
        INSERT INTO trades (ticker, action, amount_usd, price)
        VALUES ($1, $2, $3, $4)
        RETURNING id, ticker, action, amount_usd, price, timestamp;
      `;
      const values = [ticker.toUpperCase(), signal, amount_usd, current_price];
      
      const dbResult = await pool.query(query, values);
      const executedTrade = dbResult.rows[0];

      // 5. Fire Async Event to RabbitMQ
      await publishTradeEvent(executedTrade, fastify.log);

      return reply.code(201).send({
        success: true,
        message: `Successfully executed ${signal} order for ${ticker}.`,
        data: executedTrade
      });

    } catch (error) {
      fastify.log.error(`Execution Engine Error: ${error.message}`);
      
      if (error.response) {
        // Downstream Quant Engine failure
        return reply.code(502).send({
          success: false,
          error: 'Bad Gateway',
          message: 'Failed to communicate with Quant AI Engine.'
        });
      }

      return reply.code(500).send({
        success: false,
        error: 'Internal Server Error',
        message: 'A critical error occurred during trade execution.'
      });
    }
  });
}"""

    server_content = """import fastify from 'fastify';
import { env } from './config/env.js';
import { initDb, closeDb } from './services/db.js';
import { initRabbitMQ, closeRabbitMQ } from './services/rabbitmq.js';
import tradeRoutes from './routes/trade.js';

const app = fastify({
  logger: {
    level: 'info',
    timestamp: () => `,"time":"${new Date().toISOString()}"`
  }
});

// Centralized Error Handling
app.setErrorHandler((error, request, reply) => {
  app.log.error({ err: error, requestPath: request.url }, 'Global Error Handler');
  reply.status(error.statusCode || 500).send({
    success: false,
    statusCode: error.statusCode || 500,
    error: error.name || 'Internal Server Error',
    message: 'An unexpected error occurred in the Execution Service'
  });
});

// Infrastructure Health Check
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'execution-service', 
    timestamp: new Date().toISOString() 
  };
});

// Mount Routes
app.register(tradeRoutes);

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    // Await infrastructural dependencies before binding port
    app.log.info('Connecting to infrastructure...');
    await initDb(app.log);
    await initRabbitMQ(app.log);

    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 Execution Service active at http://${env.HOST}:${env.PORT}`);

    // SIGINT (Ctrl+C) & SIGTERM (Docker/K8s kill signal) Handling
    const shutdown = async (signal) => {
      app.log.info(`\nReceived ${signal}, initiating graceful shutdown...`);
      
      // 1. Stop accepting new HTTP requests
      await app.close();
      app.log.info('HTTP server closed.');
      
      // 2. Drain and close external connections
      await closeRabbitMQ();
      app.log.info('RabbitMQ connection successfully closed.');
      
      await closeDb();
      app.log.info('PostgreSQL pool successfully closed.');
      
      app.log.info('Execution Service shutdown complete. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'Execution Service failed to initialize');
    process.exit(1);
  }
};

startServer();"""

    if not package.exists():
        package.touch()
        package.write_text(package_content)
    else:
        print(f"{package} file existed...")

    if not env.exists():
        env.touch()
        env.write_text(env_content)
    else:
        print(f"{env} file existed...")

    if not env_js.exists():
        env_js.touch()
        env_js.write_text(env_js_content)
    else:
        print(f"{env_js} file existed...")

    if not db_js.exists():
        db_js.touch()
        db_js.write_text(db_js_content)
    else:
        print(f"{db_js} file existed...")

    if not rabbitmq.exists():
        rabbitmq.touch()
        rabbitmq.write_text(rabbitmq_content)
    else:
        print(f"{rabbitmq} file existed...")

    if not trade_js.exists():
        trade_js.touch()
        trade_js.write_text(trade_js_content)
    else:
        print(f"{trade_js} file existed...")

    if not server.exists():
        server.touch()
        server.write_text(server_content)
    else:
        print(f"{server} file existed...")

def notification_service():
    main = Path("notification-service")
    package = main / "package.json" # done 
    env = main / ".env" # done 
    src = main / "src" # done  
    config = src / "config" # done
    env_js = config / "env.js" # done
    services = src / "services" # done
    rabbitmq = services / "rabbitmq.js" # done 
    server = src / "server.js" # done

    if not src.exists():
        src.mkdir(parents=True)
        print(f"{src} folder created inside {main} folder...")
    else:
        print(f"{src} folder already exists...")

    if not config.exists():
        config.mkdir(parents=True)
        print(f"{config} folder created inside {src} folder...")
    else:
        print(f"{config} folder already exists...")

    if not services.exists():
        services.mkdir(parents=True)
        print(f"{services} folder created inside {src} folder...")
    else:
        print(f"{services} folder already exists...")

    package_content = """{
  "name": "notification-service",
  "version": "1.0.0",
  "description": "Background Notification Worker for QuantTrade Engine",
  "type": "module",
  "main": "src/server.js",
  "scripts": {
    "start": "node src/server.js",
    "dev": "node --watch src/server.js"
  },
  "dependencies": {
    "amqplib": "^0.10.4",
    "dotenv": "^16.4.5",
    "fastify": "^4.26.2",
    "zod": "^3.23.8"
  },
  "author": "",
  "license": "MIT"
}"""
    env_content = """# Server Configuration (For Kubernetes Health Probes)
PORT=3004
HOST=0.0.0.0

# RabbitMQ Broker Configuration
# Format: amqp://username:password@host:port
RABBITMQ_URL=amqp://localhost:5672"""
    env_js_content = """import { z } from 'zod';
import 'dotenv/config';

const envSchema = z.object({
  PORT: z.string().default('3004'),
  HOST: z.string().default('0.0.0.0'),
  RABBITMQ_URL: z.string().url('RABBITMQ_URL must be a valid AMQP connection string')
});

const parseResult = envSchema.safeParse(process.env);

if (!parseResult.success) {
  console.error(
    JSON.stringify({
      level: 'fatal',
      time: new Date().toISOString(),
      msg: 'Notification Service Environment Validation Error',
      errors: parseResult.error.format()
    })
  );
  process.exit(1);
}

export const env = parseResult.data;"""
    rabbitmq_content = """import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';

export const initRabbitMQConsumer = async (logger) => {
  let retries = 5;
  while (retries > 0) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();
      
      // Ensure the queue exists; durable means messages survive broker restarts
      await channel.assertQueue(QUEUE_NAME, { durable: true });
      
      // Ensure the worker only gets 1 message at a time to distribute load evenly
      await channel.prefetch(1);
      
      logger.info('RabbitMQ consumer initialized: listening to trade_events queue.');
      
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
      });

      // Start Consuming
      channel.consume(QUEUE_NAME, (msg) => {
        if (msg !== null) {
          try {
            const payload = JSON.parse(msg.content.toString());
            
            // Core Logic: Simulate sending a notification
            logger.info(
              `Alert: TRADE EXECUTED - TICKER: ${payload.ticker}, ACTION: ${payload.action}, AMOUNT: $${payload.amount_usd}. Notification email sent.`
            );
            
            // Acknowledge the message so it is removed from the queue
            channel.ack(msg);
          } catch (error) {
            logger.error({ err: error, content: msg.content.toString() }, 'Failed to parse RabbitMQ message. Discarding poison pill.');
            // We acknowledge even on parse failure to prevent the queue from getting stuck in an infinite retry loop
            channel.ack(msg); 
          }
        }
      });

      return;
    } catch (error) {
      retries -= 1;
      logger.warn(`RabbitMQ not ready, retrying... (${retries} attempts left)`);
      if (retries === 0) {
        logger.error(`Failed to connect to RabbitMQ: ${error.message}`);
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
};

export const closeRabbitMQ = async () => {
  try {
    if (channel) await channel.close();
    if (connection) await connection.close();
  } catch (error) {
    console.error('Error closing RabbitMQ connection', error);
  }
};"""
    server_content = """import fastify from 'fastify';
import { env } from './config/env.js';
import { initRabbitMQConsumer, closeRabbitMQ } from './services/rabbitmq.js';

const app = fastify({
  logger: {
    level: 'info',
    timestamp: () => `,"time":"${new Date().toISOString()}"`
  }
});

// Infrastructure Health Check (Crucial for Kubernetes)
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'notification-service', 
    timestamp: new Date().toISOString() 
  };
});

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    // 1. Await infrastructural dependencies before binding port
    app.log.info('Connecting to message broker...');
    await initRabbitMQConsumer(app.log);

    // 2. Bind port for liveness/readiness probes
    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 Notification Service (Worker) active at http://${env.HOST}:${env.PORT}`);

    // SIGINT (Ctrl+C) & SIGTERM (Docker/K8s kill signal) Handling
    const shutdown = async (signal) => {
      app.log.info(`\nReceived ${signal}, initiating graceful shutdown...`);
      
      // Stop accepting new HTTP requests (health checks)
      await app.close();
      app.log.info('HTTP server closed.');
      
      // Drain and close RabbitMQ consumer
      await closeRabbitMQ();
      app.log.info('RabbitMQ consumer successfully closed.');
      
      app.log.info('Notification Service shutdown complete. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'Notification Service failed to initialize');
    process.exit(1);
  }
};

startServer();"""
    if not package.exists():
        package.touch()
        package.write_text(package_content)
    else:
        print(f"{package} file existed...")
    
    if not env.exists():
        env.touch()
        env.write_text(env_content)
    else:
        print(f"{env} file existed...")
    
    if not env_js.exists():
        env_js.touch()
        env_js.write_text(env_js_content)
    else:
        print(f"{env_js} file existed...")
    
    if not rabbitmq.exists():
        rabbitmq.touch()
        rabbitmq.write_text(rabbitmq_content)
    else:
        print(f"{rabbitmq} file existed...")
    
    if not server.exists():
        server.touch()
        server.write_text(server_content)
    else:
        print(f"{server} file existed...")
api_gateway()
market_data_service()
quant_ai_engine()
execution_service()
notification_service()
