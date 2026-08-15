import fastify from 'fastify';
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
      app.log.info(`\nReceived ${signal}, initiating graceful shutdown...`);
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
