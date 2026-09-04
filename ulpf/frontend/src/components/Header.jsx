import React from 'react';
import { Shield } from 'lucide-react';
import SystemStatus from './SystemStatus';

const Header = () => {
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
            <a href="#" className="text-primary-600 font-semibold border-b-2 border-primary-600 px-1 py-5">Dashboard</a>
            <a href="#" className="text-slate-500 hover:text-slate-800 font-medium px-1 py-5 transition-colors">Process Log</a>
            <a href="#" className="text-slate-500 hover:text-slate-800 font-medium px-1 py-5 transition-colors">History</a>
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
