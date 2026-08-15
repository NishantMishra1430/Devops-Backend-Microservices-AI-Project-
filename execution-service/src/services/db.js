import pg from 'pg';
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
};