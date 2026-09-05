import React from 'react';
import { Shield } from 'lucide-react';
import SystemStatus from './SystemStatus';

const Header = ({ activeView, onNav = () => {} }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-primary-500 p-2 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 tracking-tight">ULPF</h1>
              <p className="text-xs text-slate-500 font-medium">Universal Log Pre-Processing Framework</p>
            </div>
          </div>
          
          <nav className="hidden md:flex space-x-8">
            <button onClick={() => onNav('dashboard')} className={`font-semibold px-1 py-5 border-b-2 transition-colors ${activeView === 'dashboard' ? 'text-primary-600 border-primary-600' : 'text-slate-500 hover:text-slate-800 border-transparent'}`}>Dashboard</button>
            <button onClick={() => onNav('process')} className={`font-semibold px-1 py-5 border-b-2 transition-colors ${activeView === 'process' ? 'text-primary-600 border-primary-600' : 'text-slate-500 hover:text-slate-800 border-transparent'}`}>Process Log</button>
            <button onClick={() => onNav('plugins')} className={`font-semibold px-1 py-5 border-b-2 transition-colors ${activeView === 'plugins' ? 'text-purple-600 border-purple-600' : 'text-slate-500 hover:text-slate-800 border-transparent'}`}>Plugin Registry</button>
            <button onClick={() => onNav('history')} className={`font-semibold px-1 py-5 border-b-2 transition-colors ${activeView === 'history' ? 'text-primary-600 border-primary-600' : 'text-slate-500 hover:text-slate-800 border-transparent'}`}>History</button>
          </nav>

          <div className="flex items-center">
            <SystemStatus />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
