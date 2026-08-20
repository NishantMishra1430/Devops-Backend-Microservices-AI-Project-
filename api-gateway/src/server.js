import Fastify from 'fastify';
import proxy from '@fastify/http-proxy';

const fastify = Fastify({ logger: true });

// Define public endpoints that bypass the JWT check
const PUBLIC_ROUTES = [
    '/api/auth/login', 
    '/api/auth/register', 
    '/health'
];

// --- Authentication Middleware (Border Checkpoint) ---
fastify.addHook('preHandler', async (request, reply) => {
    // 1. Allow public routes to bypass authentication
    if (PUBLIC_ROUTES.includes(request.url) || request.url.startsWith('/api/auth/')) {
        return;
    }

    // 2. Extract Authorization header
    const authHeader = request.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return reply.code(401).send({ error: 'Missing or malformed Authorization header. Bearer token required.' });
    }

    try {
        // 3. Query the internal Auth Service to validate the token
        // Using 'auth-service:8000' relies on Docker Compose internal DNS
        const response = await fetch('http://auth-service:8000/verify', {
            method: 'GET',
            headers: {
                'Authorization': authHeader
            }
        });

        if (!response.ok) {
            return reply.code(401).send({ error: 'Invalid or expired token.' });
        }

        const authData = await response.json();
        
        // 4. Inject the validated user ID into the downstream headers
        // This allows your Quant and Execution services to know exactly who made the request
        // without them having to verify the token themselves.
        request.headers['X-User-Id'] = authData.user_id;

    } catch (error) {
        request.log.error(`[Auth-Service] Connection failed: ${error.message}`);
        return reply.code(503).send({ error: 'Authentication service temporarily unavailable.' });
    }
});

// --- Microservice Route Proxies ---

// 1. Auth Service Routes (Public)
fastify.register(proxy, {
    upstream: 'http://auth-service:8000',
    prefix: '/api/auth',
    rewritePrefix: '', // Maps /api/auth/register on the Gateway to /register on the Auth Service
});

// 2. Execution Engine Routes (Protected)
fastify.register(proxy, {
    upstream: 'http://quant-execution:8000',
    prefix: '/api/execution',
    rewritePrefix: '', 
});

// 3. API Gateway Health Check (Public)
fastify.get('/health', async (request, reply) => {
    return { status: 'healthy', service: 'api-gateway' };
});

const start = async () => {
    try {
        await fastify.listen({ port: 3000, host: '0.0.0.0' });
        fastify.log.info(`API Gateway listening on port 3000`);
    } catch (err) {
        fastify.log.error(err);
        process.exit(1);
    }
};

start();
