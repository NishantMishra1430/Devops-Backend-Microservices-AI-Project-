import amqplib from 'amqplib';
import { env } from '../config/env.js';

let connection = null;
let channel = null;
const QUEUE_NAME = 'trade_events';

export const initRabbitMQConsumer = async (logger) => {
  let retries = 5;
  while (retries > 0) {
    try {
      connection = await amqplib.connect(env.RABBITMQ_URL);
      channel = await connection.createChannel();
      
      // Ensure the queue exists; durable means messages survive broker restarts
      await channel.assertQueue(QUEUE_NAME, { durable: true });
      
      // Ensure the worker only gets 1 message at a time to distribute load evenly
      await channel.prefetch(1);
      
      logger.info('RabbitMQ consumer initialized: listening to trade_events queue.');
      
      connection.on('error', (err) => {
        logger.error(`RabbitMQ connection error: ${err.message}`);
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
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
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