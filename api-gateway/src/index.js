import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

const app = express();
const PORT = process.env.PORT || 3000;

// --- Service Discovery / Routing Table ---
const SERVICES = {
    AUTH: 'http://auth-service:3006',
    MARKET: 'http://market-data-service:3001',
    QUANT: 'http://quant-engine:3002',
    EXECUTION: 'http://execution-service:3003'
};

// --- Authentication Middleware (Zero-Trust Checkpoint) ---
const requireAuth = async (req, res, next) => {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        console.warn(`[Gateway] Rejected request to ${req.originalUrl} - Missing Token`);
        return res.status(401).json({ error: 'Unauthorized: Missing or malformed Bearer token.' });
    }

    try {
        // Native fetch (Node 18+) for lightweight internal verification
        const response = await fetch(`${SERVICES.AUTH}/verify`, {
            method: 'GET',
            headers: { 'Authorization': authHeader }
        });

        if (!response.ok) {
            console.warn(`[Gateway] Rejected request to ${req.originalUrl} - Invalid Token`);
            return res.status(401).json({ error: 'Unauthorized: Invalid or expired token.' });
        }

        const authData = await response.json();
        
        // Inject the verified User ID into downstream headers.
        // This securely tells downstream services EXACTLY who is making the request.
        if (authData.user_id) {
            req.headers['x-user-id'] = authData.user_id;
        }

        next(); // Token valid, proceed to the proxy
    } catch (error) {
        console.error(`[Gateway] Auth Service Unreachable: ${error.message}`);
        return res.status(503).json({ error: 'Authentication service temporarily unavailable.' });
    }
};

// --- Proxy Configuration Factory ---
const createProxy = (targetUrl) => {
    return createProxyMiddleware({
        target: targetUrl,
        changeOrigin: true,
        // Optional: If you want /auth/login to hit /login on the auth service, uncomment the line below:
        // pathRewrite: { '^/auth': '', '^/market': '', '^/quant': '', '^/trade': '' },
        on: {
            error: (err, req, res) => {
                console.error(`[Proxy Error] Target: ${targetUrl} | Error: ${err.message}`);
                res.status(502).json({ error: 'Bad Gateway: Downstream service is unreachable.' });
            }
        }
    });
};

// --- Health Check ---
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'healthy', service: 'api-gateway' });
});

// --- Public Routes ---
// Proxies directly to Auth Service without verifying token
app.use('/auth', createProxy(SERVICES.AUTH));

// --- Protected Routes ---
// Middleware intercepts and verifies JWT before proxying
app.use('/market', requireAuth, createProxy(SERVICES.MARKET));
app.use('/quant', requireAuth, createProxy(SERVICES.QUANT));
app.use('/trade', requireAuth, createProxy(SERVICES.EXECUTION));

// --- Fallback Route ---
app.use('*', (req, res) => {
    res.status(404).json({ error: 'Route not found on API Gateway.' });
});

// --- Boot Server ---
app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Gateway] Initialization complete. Listening on port ${PORT}`);
    console.log(`[Gateway] Auth Service target set to: ${SERVICES.AUTH}`);
});
