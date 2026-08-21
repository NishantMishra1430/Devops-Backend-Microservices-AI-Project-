import { useContext } from 'react';
import { AuthContext } from './context/AuthContext';
import AuthPanel from './components/AuthPanel';
import MarketDataPanel from './components/MarketDataPanel';
import QuantEnginePanel from './components/QuantEnginePanel';
import ExecutionPanel from './components/ExecutionPanel';
import NotificationPanel from './components/NotificationPanel';

export default function App() {
  const { isAuthenticated, loading, logout } = useContext(AuthContext);

  if (loading) {
    return <div className="h-screen flex items-center justify-center font-mono text-trading-text">INITIALIZING...</div>;
  }

  if (!isAuthenticated) {
    return <AuthPanel />;
  }

  return (
    <div className="min-h-screen p-4 flex flex-col space-y-4 max-w-[1600px] mx-auto">
      {/* Top Navbar */}
      <header className="flex justify-between items-center bg-trading-panel border border-trading-border rounded-md p-4 font-mono">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-trading-green animate-pulse"></div>
          <h1 className="text-white font-bold tracking-widest">QUANT_SYS.DASHBOARD</h1>
        </div>
        <button onClick={logout} className="text-xs border border-trading-border hover:bg-trading-red/20 hover:text-trading-red hover:border-trading-red text-trading-text px-3 py-1 rounded transition-colors">
          TERMINATE_SESSION
        </button>
      </header>

      {/* Main Grid Architecture */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 flex-grow">
        <div className="col-span-1">
          <MarketDataPanel />
        </div>
        <div className="col-span-1 lg:col-span-2">
          <QuantEnginePanel />
        </div>
        <div className="col-span-1">
          <NotificationPanel />
        </div>
        
        {/* Full width row for Execution */}
        <div className="col-span-1 lg:col-span-4">
          <ExecutionPanel />
        </div>
      </div>
    </div>
  );
}