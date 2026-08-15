import { getMarketPrices } from '../services/marketMock.js';

export default async function priceRoutes(fastify, options) {
  
  const marketDataHandler = async (request, reply) => {
    try {
      const prices = await getMarketPrices();
      
      return reply.code(200).send({
        success: true,
        timestamp: new Date().toISOString(),
        data: prices
      });
    } catch (error) {
      fastify.log.error(`Failed to fetch market prices: ${error.message}`);
      return reply.code(500).send({
        success: false,
        error: 'Internal Server Error',
        message: 'Unable to retrieve live market data'
      });
    }
  };

  // Bind to root (if gateway strips prefix)
  fastify.get('/', marketDataHandler);
  
  // Bind to specific path (if gateway passes raw URI)
  fastify.get('/api/market', marketDataHandler);
}
    