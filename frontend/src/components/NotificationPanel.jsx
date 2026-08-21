import { useState, useEffect } from 'react';

export default function NotificationPanel() {
  const [logs, setLogs] = useState([
    { time: new Date().toLocaleTimeString(), msg: "System initialization complete.", type: "info" },
    { time: new Date().toLocaleTimeString(), msg: "Connected to API Gateway.", type: "info" }
  ]);

  useEffect(() => {
    // Simulating incoming socket events or system logs
    const interval = setInterval(() => {
      const messages = [
        { msg: "Redis stream synced.", type: "info" },
        { msg: "Market Data WebSocket heartbeat OK.", type: "info" },
        { msg: "Quant Engine calculated Z-Score threshold.", type: "warning" }
      ];
      const randomMsg = messages[Math.floor(Math.random() * messages.length)];
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), ...randomMsg }, ...prev].slice(0, 50));
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-trading-panel border border-trading-border rounded-md p-4 font-mono h-64 lg:h-full flex flex-col">
      <h3 className="text-sm font-bold text-white tracking-widest mb-4 border-b border-trading-border pb-2">SYS.LOGS</h3>
      <div className="flex-grow overflow-y-auto space-y-1">
        {logs.map((log, idx) => (
          <div key={idx} className="text-xs">
            <span className="text-gray-500">[{log.time}]</span>{' '}
            <span className={log.type === 'warning' ? 'text-yellow-500' : 'text-trading-text'}>{log.msg}</span>
          </div>
        ))}
      </div>
    </div>
  );
}