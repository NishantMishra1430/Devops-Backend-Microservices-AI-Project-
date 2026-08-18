import Fastify from 'fastify';
import WebSocket from 'ws';
import Redis from 'ioredis';

const fastify = Fastify({ logger: true });

// 1. Redis ke strict status trackers laga
const redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379');

redis.on('connect', () => fastify.log.info('🟢 STAGE 1: Redis TCP Connection OK!'));
redis.on('error', (err) => fastify.log.error('🔴 STAGE 1 ERROR: Redis se connect nahi ho pa raha:', err));

// Basic health check for Docker
fastify.get('/health', async (request, reply) => {
    return { status: 'OK', message: 'Market Data Producer is running' };
});

const startBinanceStream = () => {
    fastify.log.info("Attempting to connect to Binance WebSocket...");
    const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@trade');

    ws.on('open', () => {
        fastify.log.info('✅ Successfully connected to Binance Live Stream!');
    });

    // 2. Data stream ke andar aggressive logging
    ws.on('message', async (data) => {
        try {
            const trade = JSON.parse(data);
            const currentPrice = trade.p; 
            
            // Agar price ajeeb format mein aaya, toh ye pakad lega
            if (!currentPrice) {
                fastify.log.warn(`⚠️ STAGE 2 WARNING: Price nahi mila! Binance ne ye bheja: ${data}`);
                return;
            }

            // Dekh ki write function tak data pahuncha ya nahi
            fastify.log.info(`[DEBUG] STAGE 3: Redis mein $${currentPrice} likhne ki koshish kar raha hu...`);
            
            await redis.xadd('market:stream:live', '*', 'price', currentPrice);
            
            fastify.log.info(`[DEBUG] STAGE 4: SUCCESS! Redis mein likh diya!`);
            
        } catch (error) {
            // Agar xadd fail hua toh exact error yahan print hoga
            fastify.log.error('🔴 STAGE 4 ERROR: Redis xadd command fail ho gaya:', error.message);
        }
    });

    ws.on('close', () => {
        fastify.log.warn('⚠️ Binance WebSocket disconnected. Reconnecting in 5 seconds...');
        setTimeout(startBinanceStream, 5000);
    });

    ws.on('error', (err) => {
        fastify.log.error('WebSocket Error:', err.message);
    });
};

const start = async () => {
    try {
        await fastify.listen({ port: 3001, host: '0.0.0.0' });
        fastify.log.info('🚀 Market Data Service active at http://0.0.0.0:3001');
        startBinanceStream();
    } catch (err) {
        fastify.log.error(err);
        process.exit(1);
    }
};

start();