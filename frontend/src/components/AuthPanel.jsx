import { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../utils/api';

export default function AuthPanel() {
  const { login } = useContext(AuthContext);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      
      // THE BULLETPROOF PAYLOAD: 
      // Hum JSON bhej rahe hain aur 'email' + 'username' dono bhej rahe hain.
      // Isse backend Pydantic model satisfy ho jayega chahe usko kuch bhi chahiye ho!
      const response = await api.post(endpoint, { 
        email: email, 
        username: email, 
        password: password 
      });

      if (isLogin) {
        login(response.data.access_token);
      } else {
        setIsLogin(true); // Wapas login page par bhej do
        setError('Registration successful. Please log in.'); // Halka sa notification
      }
    } catch (err) {
      // TERA CRASH-PROOF ERROR HANDLER (Yeh mast chal raha hai!)
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(`Validation Error: ${detail[0].loc.join('.')} - ${detail[0].msg}`);
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Authentication failed. Please check your credentials.');
      }
    }
    
    setLoading(false);
  };
       

  return (
    <div className="flex items-center justify-center h-screen bg-trading-bg font-sans">
      <div className="bg-trading-panel border border-trading-border p-8 rounded-md w-96 shadow-2xl">
        <h2 className="text-2xl text-white font-mono mb-6">{isLogin ? 'SYSTEM.LOGIN' : 'SYSTEM.REGISTER'}</h2>
        {error && <div className="bg-trading-red/20 border border-trading-red text-trading-red text-sm p-3 rounded mb-4 font-mono">{error}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs uppercase text-trading-text mb-1 font-mono">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-trading-bg border border-trading-border text-white p-2 rounded focus:outline-none focus:border-trading-blue font-mono text-sm"
              required 
            />
          </div>
          <div>
            <label className="block text-xs uppercase text-trading-text mb-1 font-mono">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-trading-bg border border-trading-border text-white p-2 rounded focus:outline-none focus:border-trading-blue font-mono text-sm"
              required 
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-trading-blue hover:bg-blue-700 text-white font-mono py-2 px-4 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'EXECUTING...' : isLogin ? 'AUTHENTICATE' : 'INITIALIZE'}
          </button>
        </form>
        <div className="mt-4 text-center font-mono text-xs">
          <button onClick={() => setIsLogin(!isLogin)} className="text-trading-text hover:text-white transition-colors">
            {isLogin ? 'Switch to Register' : 'Switch to Login'}
          </button>
        </div>
      </div>
    </div>
  );
}
