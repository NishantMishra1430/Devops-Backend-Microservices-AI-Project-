import { z } from 'zod';
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
