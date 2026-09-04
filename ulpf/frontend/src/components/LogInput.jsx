import React, { useState } from 'react';
import { Upload, Play, Terminal } from 'lucide-react';

const EXAMPLES = {
  'Syslog': 'Sep 04 10:32:15 firewall01 sshd[1234]: Accepted publickey for user admin from 192.168.1.10 port 54321 ssh2',
  'JSON': '{"timestamp": "2026-09-04T10:32:15Z", "src_ip": "192.168.1.10", "dest_ip": "10.0.0.5", "action": "ALLOW", "severity": "medium"}',
  'CEF': 'CEF:0|Security|Firewall|1.0|100|Traffic Allowed|3|src=192.168.1.10 dst=10.0.0.5 spt=443 dpt=80 act=ALLOW',
  'LEEF': 'LEEF:1.0|Security|Firewall|1.0|100|src=192.168.1.10\tdst=10.0.0.5\tact=ALLOW',
  'Key-Value': 'time="2026-09-04 10:32:15" action=ALLOW src=192.168.1.10 dst=10.0.0.5',
  'CSV': '2026-09-04T10:32:15,192.168.1.10,10.0.0.5,ALLOW',
  'Unknown / Custom': '2026-09-04 10:32:15 | 192.168.1.10 | 10.0.0.5 | 443 | ALLOW',
  'Malformed': '{"timestamp": "2026-09-04T10:32:15Z", "src_ip": "192.168.1.10", "dest_ip": "10.0.0.5", "action": "ALLOW"' // missing closing brace
};

const LogInput = ({ onProcess, isProcessing }) => {
  const [logText, setLogText] = useState('');
  
  const handleProcess = () => {
    if (logText.trim()) {
      onProcess(logText);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100">
        <h2 className="text-xl font-bold text-slate-800 mb-2">Process a Security Log</h2>
        <p className="text-slate-500 text-sm">Paste a raw log event or select an example to begin processing.</p>
      </div>
      
      <div className="p-6 bg-slate-50">
        <div className="flex space-x-2 mb-4 overflow-x-auto pb-2">
          {Object.entries(EXAMPLES).map(([name, text]) => (
            <button
              key={name}
              onClick={() => setLogText(text)}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-600 rounded-full hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 transition-colors whitespace-nowrap"
            >
              {name}
            </button>
          ))}
        </div>

        <div className="relative">
          <div className="absolute top-3 left-3 text-slate-400">
            <Terminal className="w-5 h-5" />
          </div>
          <textarea
            value={logText}
            onChange={(e) => setLogText(e.target.value)}
            placeholder="Paste a raw log event here..."
            className="w-full h-48 pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm resize-none"
            spellCheck="false"
          />
        </div>

        <div className="mt-4 flex justify-between items-center">
          <button className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800">
            <Upload className="w-4 h-4" />
            <span>Upload File</span>
          </button>
          
          <button
            onClick={handleProcess}
            disabled={!logText.trim() || isProcessing}
            className="flex items-center space-x-2 px-6 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors shadow-sm"
          >
            {isProcessing ? (
              <>
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Process Log</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogInput;
