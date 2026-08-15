import fastify from 'fastify';
import { env } from './config/env.js';
import { initDb, closeDb } from './services/db.js';
import { initRabbitMQ, closeRabbitMQ } from './services/rabbitmq.js';
import tradeRoutes from './routes/trade.js';

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
    message: 'An unexpected error occurred in the Execution Service'
  });
});

// Infrastructure Health Check
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'execution-service', 
    timestamp: new Date().toISOString() 
  };
});

// Mount Routes
app.register(tradeRoutes);

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    // Await infrastructural dependencies before binding port
    app.log.info('Connecting to infrastructure...');
    await initDb(app.log);
    await initRabbitMQ(app.log);

    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 Execution Service active at http://${env.HOST}:${env.PORT}`);

    // SIGINT (Ctrl+C) & SIGTERM (Docker/K8s kill signal) Handling
    const shutdown = async (signal) => {
      app.log.info(`
Received ${signal}, initiating graceful shutdown...`);
      
      // 1. Stop accepting new HTTP requests
      await app.close();
      app.log.info('HTTP server closed.');
      
      // 2. Drain and close external connections
      await closeRabbitMQ();
      app.log.info('RabbitMQ connection successfully closed.');
      
      await closeDb();
      app.log.info('PostgreSQL pool successfully closed.');
      
      app.log.info('Execution Service shutdown complete. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'Execution Service failed to initialize');
    process.exit(1);
  }
};

startServer();