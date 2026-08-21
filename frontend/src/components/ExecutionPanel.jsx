export default function ExecutionPanel() {
  // Simulated portfolio state
  const portfolio = {
    cash: 10450.25,
    value: 12500.50,
    pnl: 2500.50,
    pnlPct: 25.0
  };

  const positions = [
    { symbol: 'BTCUSDT', side: 'LONG', qty: 0.032, entry: 64100.50, current: 64500.00 },
  ];

  const pnlColor = portfolio.pnl >= 0 ? 'text-trading-green' : 'text-trading-red';

  return (
    <div className="bg-trading-panel border border-trading-border rounded-md p-4 font-mono col-span-1 lg:col-span-2">
      <h3 className="text-sm font-bold text-white tracking-widest mb-4 border-b border-trading-border pb-2">EXECUTION.PORTFOLIO</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-trading-bg p-3 border border-trading-border rounded">
          <div className="text-xs text-trading-text">Total Value</div>
          <div className="text-lg text-white">${portfolio.value.toFixed(2)}</div>
        </div>
        <div className="bg-trading-bg p-3 border border-trading-border rounded">
          <div className="text-xs text-trading-text">Cash Balance</div>
          <div className="text-lg text-white">${portfolio.cash.toFixed(2)}</div>
        </div>
        <div className="bg-trading-bg p-3 border border-trading-border rounded">
          <div className="text-xs text-trading-text">Unrealized PnL</div>
          <div className={`text-lg ${pnlColor}`}>${portfolio.pnl.toFixed(2)}</div>
        </div>
        <div className="bg-trading-bg p-3 border border-trading-border rounded">
          <div className="text-xs text-trading-text">ROI</div>
          <div className={`text-lg ${pnlColor}`}>{portfolio.pnlPct.toFixed(2)}%</div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-trading-text">
          <thead className="text-xs uppercase bg-trading-bg border-y border-trading-border">
            <tr>
              <th className="px-4 py-2">Symbol</th>
              <th className="px-4 py-2">Side</th>
              <th className="px-4 py-2">Qty</th>
              <th className="px-4 py-2">Entry</th>
              <th className="px-4 py-2">Current</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos, idx) => (
              <tr key={idx} className="border-b border-trading-border/50 hover:bg-trading-border/30">
                <td className="px-4 py-2 text-white">{pos.symbol}</td>
                <td className={`px-4 py-2 ${pos.side === 'LONG' ? 'text-trading-green' : 'text-trading-red'}`}>{pos.side}</td>
                <td className="px-4 py-2">{pos.qty}</td>
                <td className="px-4 py-2">${pos.entry.toFixed(2)}</td>
                <td className="px-4 py-2">${pos.current.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}