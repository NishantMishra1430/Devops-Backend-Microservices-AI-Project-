import { z } from 'zod';
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
    