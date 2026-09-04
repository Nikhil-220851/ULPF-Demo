import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, Copy } from 'lucide-react';

const SummaryCard = ({ label, value, subtext, status }) => (
  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
    <div className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">{label}</div>
    <div className="text-lg font-bold text-slate-800 flex items-center gap-2">
      {status === 'success' && <CheckCircle className="w-5 h-5 text-green-500" />}
      {status === 'warning' && <AlertTriangle className="w-5 h-5 text-orange-500" />}
      {status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
      {value}
    </div>
    {subtext && <div className="text-xs text-slate-400 mt-1">{subtext}</div>}
  </div>
);

const ResultView = ({ result }) => {
  const [activeTab, setActiveTab] = useState('normalized');

  if (!result || result.status === 'not implemented') {
    return (
      <div className="bg-orange-50 p-6 rounded-xl border border-orange-200 text-center">
        <AlertTriangle className="w-8 h-8 text-orange-500 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-orange-800">Endpoint Not Implemented</h3>
        <p className="text-sm text-orange-600 mt-2">
          The backend API returned a "not implemented" status. 
          To see the full pipeline, please implement the parsing and normalization logic in the Python backend.
        </p>
      </div>
    );
  }

  // Defensive fallback data just in case the backend doesn't provide them but is not strictly "not implemented"
  const detectedFormat = result?.detected_format || 'Unknown';
  const confidence = result?.confidence?.overall || 'N/A';
  const validationStatus = result?.validation?.status || 'UNKNOWN';
  
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard label="Format" value={detectedFormat} status="success" />
        <SummaryCard label="Confidence" value={confidence + '%'} status={confidence > 80 ? 'success' : 'warning'} />
        <SummaryCard label="Validation" value={validationStatus} status={validationStatus === 'VALID' ? 'success' : 'error'} />
        <SummaryCard label="Status" value="PROCESSED" status="success" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="flex border-b border-slate-200">
          <button 
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'normalized' ? 'border-primary-500 text-primary-600 bg-primary-50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
            onClick={() => setActiveTab('normalized')}
          >
            Universal Event
          </button>
          <button 
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'unmapped' ? 'border-primary-500 text-primary-600 bg-primary-50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
            onClick={() => setActiveTab('unmapped')}
          >
            Unmapped Fields
          </button>
          <button 
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'raw' ? 'border-primary-500 text-primary-600 bg-primary-50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
            onClick={() => setActiveTab('raw')}
          >
            Raw Event
          </button>
          <button 
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'traceability' ? 'border-primary-500 text-primary-600 bg-primary-50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
            onClick={() => setActiveTab('traceability')}
          >
            Traceability
          </button>
        </div>

        <div className="p-6">
          {activeTab === 'normalized' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Normalized Fields</h3>
                <button className="flex items-center space-x-1 text-sm text-slate-500 hover:text-primary-600">
                  <Copy className="w-4 h-4" />
                  <span>Copy JSON</span>
                </button>
              </div>
              <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 font-mono text-sm overflow-x-auto">
                <pre>{JSON.stringify(result.normalized_event || {}, null, 2)}</pre>
              </div>
            </div>
          )}

          {activeTab === 'unmapped' && (
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Unmapped Fields</h3>
              <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 font-mono text-sm overflow-x-auto">
                <pre>{JSON.stringify(result.unmapped_fields || {}, null, 2)}</pre>
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div>
              <div className="flex items-center space-x-2 mb-4 bg-blue-50 text-blue-700 p-3 rounded-lg border border-blue-200">
                <Info className="w-5 h-5" />
                <span className="text-sm font-medium">Original event preserved for forensic traceability.</span>
              </div>
              <div className="bg-slate-900 text-slate-50 p-4 rounded-lg font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                {result.raw_event}
              </div>
            </div>
          )}
          
          {activeTab === 'traceability' && (
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Field Traceability</h3>
              {result.provenance && Object.keys(result.provenance).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(result.provenance).map(([key, prov]) => (
                    <div key={key} className="flex items-center text-sm font-mono bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-primary-600 font-bold w-1/3">{key}</span>
                      <span className="text-slate-400 mx-4">←</span>
                      <span className="text-slate-600 w-1/3">{prov.original_field}</span>
                      <span className="text-slate-400 mx-4">←</span>
                      <span className="text-slate-800 w-1/3 truncate">{prov.original_value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500 italic">
                  Traceability information not available for this event.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Validation Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50">
          <h3 className="text-lg font-semibold text-slate-800">Data Quality & Validation</h3>
        </div>
        <div className="p-6">
          {validationStatus === 'VALID' ? (
             <div className="flex items-center space-x-2 text-green-600">
               <CheckCircle className="w-5 h-5" />
               <span className="font-medium">All fields passed schema validation.</span>
             </div>
          ) : (
             <div className="space-y-4">
                <div className="flex items-center space-x-2 text-red-600 font-medium">
                  <XCircle className="w-5 h-5" />
                  <span>Processing Failed</span>
                </div>
                <div className="text-sm text-slate-600 bg-red-50 p-4 rounded-lg border border-red-100">
                  <span className="font-semibold text-red-800 block mb-1">Reason:</span>
                  {result?.validation?.reason || "Validation errors occurred."}
                </div>
                <div className="text-xs font-medium text-slate-500 mt-2 flex items-center">
                   <Info className="w-4 h-4 mr-1"/>
                   Raw event preserved in Lossless tab.
                </div>
             </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultView;
