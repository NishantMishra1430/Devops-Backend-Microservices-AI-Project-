import { z } from 'zod';
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

export const env = parseResult.data;