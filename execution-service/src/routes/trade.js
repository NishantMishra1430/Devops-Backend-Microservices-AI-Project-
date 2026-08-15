import axios from 'axios';
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
}