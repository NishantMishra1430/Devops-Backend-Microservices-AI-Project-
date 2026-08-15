import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';

export const initRabbitMQ = async (logger) => {
  let retries = 5;
  while (retries > 0) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();
      
      // Ensure the queue exists before we try to publish to it
      await channel.assertQueue(QUEUE_NAME, { durable: true });
      
      logger.info('RabbitMQ initialized: connection established and queue verified.');
      
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
      });
      
      return;
    } catch (error) {
      retries -= 1;
      logger.warn(`RabbitMQ not ready, retrying... (${retries} attempts left)`);
      if (retries === 0) {
        logger.error(`Failed to connect to RabbitMQ: ${error.message}`);
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }
};

export const publishTradeEvent = async (tradePayload, logger) => {
  if (!channel) {
    throw new Error('RabbitMQ channel is not initialized');
  }
  
  const message = Buffer.from(JSON.stringify(tradePayload));
  const published = channel.sendToQueue(QUEUE_NAME, message, {
    persistent: true,
    messageId: tradePayload.id 
  });
  
  if (published) {
    logger.info({ tradeId: tradePayload.id }, 'Trade event published to RabbitMQ successfully.');
  } else {
    logger.error({ tradeId: tradePayload.id }, 'RabbitMQ buffer full, failed to publish trade event.');
  }
};

export const closeRabbitMQ = async () => {
  try {
    if (channel) await channel.close();
    if (connection) await connection.close();
  } catch (error) {
    console.error('Error closing RabbitMQ connection', error);
  }
};