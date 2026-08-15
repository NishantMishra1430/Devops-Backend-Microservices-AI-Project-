import Redis from 'ioredis';
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
    