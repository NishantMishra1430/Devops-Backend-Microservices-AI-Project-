import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';
let isShuttingDown = false; // Prevents reconnect loops during pod termination

export const initRabbitMQConsumer = async (logger) => {
  // OPTIMIZATION: Extended startup tolerance for RabbitMQ cold-boots
  let retries = 15;
  const retryDelayMs = 5000;

  while (retries > 0 && !isShuttingDown) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();

      // Ensure the queue exists; durable means messages survive broker restarts
      await channel.assertQueue(QUEUE_NAME, { durable: true });

      // Ensure the worker only gets 1 message at a time to distribute load evenly
      await channel.prefetch(1);

      logger.info('RabbitMQ consumer initialized: listening to trade_events queue.');

      // OPTIMIZATION: Handle Day-2 operational crashes automatically
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
      });

      connection.on('close', () => {
        if (!isShuttingDown) {
          logger.warn('RabbitMQ connection closed abruptly. Reconnecting in 5s...');
          channel = null;
          setTimeout(() => initRabbitMQConsumer(logger).catch(logger.error), retryDelayMs);
        }
      });

      // Start Consuming
      channel.consume(QUEUE_NAME, (msg) => {
        if (msg !== null) {
          try {
            const payload = JSON.parse(msg.content.toString());

            // Core Logic: Simulate sending a notification
            logger.info(
              `Alert: TRADE EXECUTED - TICKER: ${payload.ticker}, ACTION: ${payload.action}, AMOUNT: $${payload.amount_usd}. Notification email sent.`
            );

            // Acknowledge the message so it is removed from the queue
            channel.ack(msg);
          } catch (error) {
            logger.error({ err: error, content: msg.content.toString() }, 'Failed to parse RabbitMQ message. Discarding poison pill.');
            // We acknowledge even on parse failure to prevent the queue from getting stuck in an infinite retry loop
            channel.ack(msg);
          }
        }
      });

      return;
    } catch (error) {
      retries -= 1;
      logger.warn(`RabbitMQ not ready, retrying... (${retries} attempts left)`);
      
      if (retries === 0) {
        logger.error(`Failed to connect to RabbitMQ: ${error.message}`);
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, retryDelayMs));
    }
  }
};

export const closeRabbitMQ = async (logger = console) => {
  isShuttingDown = true; 
  try {
    if (channel) {
      await channel.close();
      if (logger.info) logger.info('RabbitMQ consumer channel closed gracefully.');
    }
    if (connection) {
      await connection.close();
      if (logger.info) logger.info('RabbitMQ consumer connection closed gracefully.');
    }
  } catch (error) {
    if (logger.error) logger.error(`Error closing RabbitMQ connection: ${error.message}`);
    else console.error('Error closing RabbitMQ connection', error);
  }
};
