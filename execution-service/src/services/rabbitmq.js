import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';
let isShuttingDown = false; // Prevents reconnect loops during pod termination

export const initRabbitMQ = async (logger) => {
  // OPTIMIZATION 1: Increased tolerances for cold-booting on a single VPS
  let retries = 15; 
  const retryDelayMs = 5000; 

  while (retries > 0 && !isShuttingDown) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();

      await channel.assertQueue(QUEUE_NAME, { durable: true });

      logger.info('RabbitMQ initialized: connection established and queue verified.');

      // OPTIMIZATION 2: Day-2 Resilience (Auto-reconnect on crash)
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
        // Connection error usually emits a 'close' event right after, 
        // which our 'close' listener will catch to trigger the reconnect.
      });

      connection.on('close', () => {
        if (!isShuttingDown) {
          logger.warn('RabbitMQ connection closed abruptly. Reconnecting in 5s...');
          channel = null; // Invalidate the dead channel
          setTimeout(() => initRabbitMQ(logger).catch(logger.error), retryDelayMs);
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
      // Wait before trying again
      await new Promise(resolve => setTimeout(resolve, retryDelayMs));
    }
  }
};

export const publishTradeEvent = async (tradePayload, logger) => {
  // OPTIMIZATION 3: Failsafe if the app tries to publish during a reconnect window
  if (!channel) {
    logger.error({ tradeId: tradePayload.id }, 'RabbitMQ channel down. Cannot publish trade event.');
    throw new Error('RabbitMQ channel is not initialized or currently reconnecting');
  }

  try {
    const message = Buffer.from(JSON.stringify(tradePayload));
    
    // sendToQueue returns false if the connection buffer is full (TCP backpressure)
    const published = channel.sendToQueue(QUEUE_NAME, message, {
      persistent: true,
      messageId: tradePayload.id
    });

    if (published) {
      logger.info({ tradeId: tradePayload.id }, 'Trade event published to RabbitMQ successfully.');
    } else {
      // If false, the message is buffered in memory, but we should log it for SRE visibility
      logger.warn({ tradeId: tradePayload.id }, 'RabbitMQ buffer full, message queued in local memory.');
    }
  } catch (error) {
    logger.error({ tradeId: tradePayload.id, err: error.message }, 'Failed to publish trade event');
    throw error;
  }
};

export const closeRabbitMQ = async (logger) => {
  isShuttingDown = true; 
  try {
    if (channel) {
      await channel.close();
      logger.info('RabbitMQ channel closed gracefully.');
    }
    if (connection) {
      await connection.close();
      logger.info('RabbitMQ connection closed gracefully.');
    }
  } catch (error) {
    logger.error(`Error closing RabbitMQ connection: ${error.message}`);
  }
};
