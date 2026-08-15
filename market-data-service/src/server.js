import fastify from 'fastify';
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
      app.log.info(`
Received ${signal}, initiating graceful shutdown...`);
      
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

startServer();