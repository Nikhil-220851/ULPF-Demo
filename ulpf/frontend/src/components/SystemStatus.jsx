import React, { useState, useEffect } from 'react';
import { checkHealth } from '../api/client';
import { Activity, CheckCircle, XCircle } from 'lucide-react';

const SystemStatus = () => {
  const [status, setStatus] = useState('Checking...');
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await checkHealth();
        if (data.status === 'ok') {
          setStatus('Backend Connected');
          setIsOnline(true);
        } else {
          setStatus('Degraded');
          setIsOnline(false);
        }
      } catch (err) {
        setStatus('Backend Offline');
        setIsOnline(false);
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-full border shadow-sm">
      <Activity className="w-4 h-4 text-slate-500" />
      <span className="text-sm font-medium text-slate-700">{status}</span>
      {isOnline ? (
        <CheckCircle className="w-4 h-4 text-green-500" />
      ) : (
        <XCircle className="w-4 h-4 text-red-500" />
      )}
    </div>
  );
};

export default SystemStatus;
