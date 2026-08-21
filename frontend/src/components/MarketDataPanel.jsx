import { useState, useEffect } from 'react';
import api from '../utils/api';

export default function MarketDataPanel() {
  const [price, setPrice] = useState(0);
  const [prevPrice, setPrevPrice] = useState(0);

  // Simulating live feed polling from the gateway for UI purposes
  useEffect(() => {
    const fetchMarketData = async () => {
      // In production, connect this to the WebSocket service or an API Gateway polling route
      // For now, generating a simulated realistic fluctuation around a baseline
      setPrevPrice(p => price || 64000);
      setPrice(prev => (prev === 0 ? 64000 : prev + (Math.random() - 0.5) * 50));
    };
    const interval = setInterval(fetchMarketData, 2000);
    return () => clearInterval(interval);
  }, [price]);

  const isUp = price >= prevPrice;

  return (
    <div className="bg-trading-panel border border-trading-border rounded-md p-4 flex flex-col font-mono h-full">
      <div className="flex justify-between items-center mb-4 border-b border-trading-border pb-2">
        <h3 className="text-sm font-bold text-white tracking-widest">MARKET.FEED</h3>
        <span className="text-xs text-trading-green animate-pulse">● LIVE</span>
      </div>
      
      <div className="flex-grow flex flex-col justify-center items-center">
        <span className="text-xs text-trading-text mb-1">BTC/USDT</span>
        <span className={`text-4xl font-bold ${isUp ? 'text-trading-green' : 'text-trading-red'}`}>
          ${price.toFixed(2)}
        </span>
        <span className="text-xs text-trading-text mt-2">
          Vol: {(Math.random() * 100).toFixed(3)} BTC
        </span>
      </div>
    </div>
  );
}