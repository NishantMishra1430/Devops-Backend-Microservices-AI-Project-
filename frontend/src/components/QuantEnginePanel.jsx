import { useState } from 'react';
import api from '../utils/api';

export default function QuantEnginePanel() {
  const [metrics, setMetrics] = useState({ variance: 0, signal: 'HOLD', confidence: 0 });
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      // Proxies through API Gateway to quant-engine:3002
      // const res = await api.get('/quant/metrics');
      // setMetrics(res.data);
      
      // Simulating response for UI layout
      setTimeout(() => {
        setMetrics({
          variance: 52.41,
          signal: Math.random() > 0.5 ? 'BUY' : 'SELL',
          confidence: (Math.random() * 100).toFixed(1)
        });
        setLoading(false);
      }, 500);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const signalColor = metrics.signal === 'BUY' ? 'text-trading-green' : metrics.signal === 'SELL' ? 'text-trading-red' : 'text-white';

  return (
    <div className="bg-trading-panel border border-trading-border rounded-md p-4 flex flex-col font-mono h-full">
      <div className="flex justify-between items-center mb-4 border-b border-trading-border pb-2">
        <h3 className="text-sm font-bold text-white tracking-widest">QUANT.ENGINE</h3>
        <button 
          onClick={fetchMetrics} 
          disabled={loading}
          className="text-xs bg-trading-border hover:bg-gray-600 text-white px-2 py-1 rounded transition-colors"
        >
          {loading ? 'CALCULATING...' : 'FORCE_EVAL'}
        </button>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between border-b border-trading-border/50 pb-2">
          <span className="text-trading-text text-sm">Target Asset</span>
          <span className="text-white text-sm">BTCUSDT</span>
        </div>
        <div className="flex justify-between border-b border-trading-border/50 pb-2">
          <span className="text-trading-text text-sm">Z-Score Var</span>
          <span className="text-white text-sm">{metrics.variance}</span>
        </div>
        <div className="flex justify-between border-b border-trading-border/50 pb-2">
          <span className="text-trading-text text-sm">Signal Output</span>
          <span className={`text-sm font-bold ${signalColor}`}>{metrics.signal}</span>
        </div>
        <div className="flex justify-between border-b border-trading-border/50 pb-2">
          <span className="text-trading-text text-sm">Confidence</span>
          <span className="text-trading-blue text-sm">{metrics.confidence}%</span>
        </div>
      </div>
    </div>
  );
}