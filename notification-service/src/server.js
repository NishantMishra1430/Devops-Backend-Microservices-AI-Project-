import fastify from 'fastify';
import { env } from './config/env.js';
import { initRabbitMQConsumer, closeRabbitMQ } from './services/rabbitmq.js';

const app = fastify({
  logger: {
    level: 'info',
    timestamp: () => `,"time":"${new Date().toISOString()}"`
  }
});

// Infrastructure Health Check (Crucial for Kubernetes)
app.get('/health', async (request, reply) => {
  return { 
    status: 'operational', 
    service: 'notification-service', 
    timestamp: new Date().toISOString() 
  };
});

// Bootstrap & Graceful Shutdown
const startServer = async () => {
  try {
    // 1. Await infrastructural dependencies before binding port
    app.log.info('Connecting to message broker...');
    await initRabbitMQConsumer(app.log);

    // 2. Bind port for liveness/readiness probes
    await app.listen({ port: parseInt(env.PORT, 10), host: env.HOST });
    app.log.info(`🚀 Notification Service (Worker) active at http://${env.HOST}:${env.PORT}`);

    // SIGINT (Ctrl+C) & SIGTERM (Docker/K8s kill signal) Handling
    const shutdown = async (signal) => {
      app.log.info(`
Received ${signal}, initiating graceful shutdown...`);
      
      // Stop accepting new HTTP requests (health checks)
      await app.close();
      app.log.info('HTTP server closed.');
      
      // Drain and close RabbitMQ consumer
      await closeRabbitMQ();
      app.log.info('RabbitMQ consumer successfully closed.');
      
      app.log.info('Notification Service shutdown complete. Exiting process.');
      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

  } catch (err) {
    app.log.error({ err }, 'Notification Service failed to initialize');
    process.exit(1);
  }
};

startServer();