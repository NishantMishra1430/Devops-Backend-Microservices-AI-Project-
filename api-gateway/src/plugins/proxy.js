import httpProxy from '@fastify/http-proxy';
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
