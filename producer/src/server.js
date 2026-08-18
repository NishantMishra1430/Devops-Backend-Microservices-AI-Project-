import WebSocket from 'ws';
import Redis from 'ioredis';

// Strictly utilize the environment variable for production orchestration
const REDIS_URL = process.env.REDIS_URL;
if (!REDIS_URL) {
    console.error('[FATAL] REDIS_URL environment variable is strictly required.');
    process.exit(1);
}

const redis = new Redis(REDIS_URL);
const STREAM_KEY = 'market:stream:live';
const BINANCE_WS_URL = 'wss://stream.binance.com:9443/ws/btcusdt@trade';

console.log(`[Network] Establishing live connection to ${BINANCE_WS_URL}`);
const ws = new WebSocket(BINANCE_WS_URL);

ws.on('open', () => {
    console.log('[Network] Live Binance WebSocket stream connected successfully.');
});

ws.on('message', async (data) => {
    try {
        const trade = JSON.parse(data);
        
        // Extract the actual execution price from the live Binance payload
        if (trade.p) {
            const actualPrice = parseFloat(trade.p);
            
            // Execute ACTUAL XADD command. Utilizing MAXLEN to prevent memory overflow in production.
            const messageId = await redis.xadd(
                STREAM_KEY, 
                'MAXLEN', '~', 1000, 
                '*', 
                'price', actualPrice
            );
            
            // Strictly logging the confirmed Redis ingestion, not just the network receipt
            console.log(`[Redis: XADD SUCCESS] ID: ${messageId} | Asset: BTCUSDT | Actual Price: $${actualPrice}`);
        }
    } catch (error) {
        console.error(`[Data Pipeline Error] Failed to process or insert live data: ${error.message}`);
    }
});

// Container lifecycle management: Crash the pod on disconnect to allow K8s to trigger a clean restart
ws.on('close', () => {
    console.error('[Network] Binance WebSocket connection dropped. Terminating process for orchestrator restart.');
    process.exit(1); 
});

ws.on('error', (error) => {
    console.error(`[Network] Fatal WebSocket Error: ${error.message}`);
    process.exit(1);
});

// Clean teardown for container SIGTERM signals
process.on('SIGTERM', async () => {
    console.log('[OS] SIGTERM received. Draining connections...');
    ws.close();
    await redis.quit();
    process.exit(0);
});