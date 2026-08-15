import { redis } from './redis.js';

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
};