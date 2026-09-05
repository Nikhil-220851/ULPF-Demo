import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LogInput from './components/LogInput';
import Pipeline from './components/Pipeline';
import ResultView from './components/ResultView';
import BatchResultView from './components/BatchResultView';
import PluginRegistry from './components/PluginRegistry';
import { processLog, processBatch } from './api/client';
import { Clock, CheckCircle, XCircle, AlertTriangle, Puzzle, FileText } from 'lucide-react';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStage, setPipelineStage] = useState(null);
  const [result, setResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [lastPluginCreated, setLastPluginCreated] = useState(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem('ulpf_history');
      if (saved) setHistory(JSON.parse(saved));
    } catch { /* ignore */ }
  }, []);

  const saveEntryToHistory = (entry) => {
    setHistory(prev => {
      const updated = [entry, ...prev].slice(0, 200);
      try { localStorage.setItem('ulpf_history', JSON.stringify(updated)); } catch { }
      return updated;
    });
  };

  const handleProcess = async (rawPayload) => {
    setActiveView('process');
    setIsProcessing(true);
    setResult(null);
    setBatchResult(null);
    setError(null);
    setPipelineStage(null);

    try {
      const data = await processLog(rawPayload);
      setPipelineStage('universal');
      setResult(data);
      saveEntryToHistory({
        id: Date.now(),
        timestamp: new Date().toLocaleString(),
        format: data.detected_format,
        validation: data.validation?.status || 'UNKNOWN',
        confidence: data.confidence?.overall || 0,
        raw: data.raw_event,
        data,
      });
    } catch (err) {
      setPipelineStage('validate');
      setError(err?.response?.data?.detail || err?.message || 'Unable to connect to the ULPF processing service.');
    } finally {
      setIsProcessing(false);
    }
  };

  // events: array of strings OR objects {raw_payload, source_file, source_file_index}
  const handleBatchProcess = async (events) => {
    setActiveView('process');
    setIsProcessing(true);
    setResult(null);
    setBatchResult(null);
    setError(null);
    setPipelineStage(null);

    try {
      const data = await processBatch(events);
      setPipelineStage('universal');
      setBatchResult(data);

      (data.results || []).forEach(r => {
        saveEntryToHistory({
          id: Date.now() + Math.random(),
          timestamp: new Date().toLocaleString(),
          format: r.detected_format,
          validation: r.validation?.status || 'UNKNOWN',
          confidence: r.confidence?.overall || 0,
          raw: r.raw_event,
          source_file: r.source_file || null,
          data: r,
        });
      });
    } catch (err) {
      setPipelineStage('validate');
      setError(err?.response?.data?.detail || err?.message || 'Batch processing failed. Check backend connectivity.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePluginConfirmed = (plugin) => {
    setLastPluginCreated(plugin);
  };

  const handleReplay = (item) => {
    setActiveView('process');
    setResult(item.data);
    setBatchResult(null);
    setPipelineStage('universal');
  };

  // Stats — event-based, not file-based
  const totalEvents = history.length;
  const validCount = history.filter(h => h.validation === 'VALID').length;
  const quarantinedCount = history.filter(h => h.validation !== 'VALID').length;
  const filesProcessed = new Set(history.map(h => h.source_file).filter(Boolean)).size;

  return (
    <div className="min-h-screen bg-background text-slate-800">
      <Header activeView={activeView} onNav={(view) => setActiveView(view)} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {/* DASHBOARD */}
        {activeView === 'dashboard' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-3xl font-bold tracking-tight mb-2">Operational Dashboard</h2>
              <p className="text-slate-500">Overview of the Universal Log Pre-Processing Framework.</p>
            </div>

            {quarantinedCount > 0 ? (
              <div className="bg-red-50 rounded-xl p-6 border border-red-200 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="bg-red-100 p-3 rounded-full"><AlertTriangle className="w-8 h-8 text-red-600" /></div>
                  <div>
                    <h3 className="text-lg font-bold text-red-900">Quarantined Events</h3>
                    <p className="text-red-700">{quarantinedCount} event(s) require attention</p>
                  </div>
                </div>
                <button onClick={() => setActiveView('history')} className="px-4 py-2 bg-white text-red-700 font-medium rounded-lg border border-red-200 hover:bg-red-50 transition-colors">
                  View in History
                </button>
              </div>
            ) : (
              <div className="bg-green-50 rounded-xl p-6 border border-green-200 flex items-center gap-4 shadow-sm">
                <div className="bg-green-100 p-3 rounded-full"><CheckCircle className="w-8 h-8 text-green-600" /></div>
                <div>
                  <h3 className="text-lg font-bold text-green-900">All Systems Normal</h3>
                  <p className="text-green-700">No quarantined events require attention.</p>
                </div>
              </div>
            )}

            {lastPluginCreated && (
              <div className="bg-purple-50 rounded-xl p-6 border border-purple-200 flex justify-between items-center shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="bg-purple-100 p-3 rounded-full"><Puzzle className="w-8 h-8 text-purple-600" /></div>
                  <div>
                    <h3 className="text-lg font-bold text-purple-900">New Plugin Created</h3>
                    <p className="text-purple-700">"{lastPluginCreated.name}" — future matching events will be parsed automatically.</p>
                  </div>
                </div>
                <button onClick={() => setActiveView('plugins')} className="px-4 py-2 bg-white text-purple-700 font-medium rounded-lg border border-purple-200 hover:bg-purple-50 transition-colors">
                  View Plugin Registry
                </button>
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-sm font-medium text-slate-500 mb-1">Events Processed</p>
                <p className="text-3xl font-bold text-slate-800">{totalEvents}</p>
              </div>
              {filesProcessed > 0 && (
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <p className="text-sm font-medium text-slate-500 mb-1">Files Processed</p>
                  <p className="text-3xl font-bold text-slate-800">{filesProcessed}</p>
                </div>
              )}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-sm font-medium text-slate-500 mb-1">Valid Events</p>
                <p className="text-3xl font-bold text-green-600">{validCount}</p>
              </div>
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <p className="text-sm font-medium text-slate-500 mb-1">Quarantined</p>
                <p className={`text-3xl font-bold ${quarantinedCount > 0 ? 'text-red-600' : 'text-slate-400'}`}>{quarantinedCount}</p>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-bold mb-4">Pipeline Overview</h3>
              <div className="flex items-center justify-between text-sm font-medium text-slate-600 px-8 py-4 bg-slate-50 rounded-lg flex-wrap gap-2">
                <span>Raw Log</span><span className="text-slate-300">→</span>
                <span>Event Extraction</span><span className="text-slate-300">→</span>
                <span>Per-Event Detection</span><span className="text-slate-300">→</span>
                <span>Parser Routing</span><span className="text-slate-300">→</span>
                <span>Normalization</span><span className="text-slate-300">→</span>
                <span>Validation</span><span className="text-slate-300">→</span>
                <span className="font-bold text-primary-600">Universal Event</span>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-lg font-bold mb-4">Supported Formats</h3>
              <div className="flex flex-wrap gap-2">
                {['CEF', 'JSON', 'Syslog', 'LEEF', 'Key-Value', 'CSV', 'Unknown / Custom', 'Custom Plugins'].map(fmt => (
                  <span key={fmt} className="px-3 py-1 bg-slate-100 text-slate-700 rounded-md text-sm font-medium border border-slate-200">{fmt}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* PROCESS LOG */}
        {activeView === 'process' && (
          <div className="space-y-8">
            <LogInput
              onProcess={handleProcess}
              onBatchProcess={handleBatchProcess}
              isProcessing={isProcessing}
            />

            {(pipelineStage || result || batchResult || error) && (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                {!batchResult && (
                  <Pipeline currentStage={pipelineStage} result={result} />
                )}

                {batchResult && (
                  <div className="mb-6">
                    <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-700 font-medium flex-wrap gap-y-2">
                      <FileText className="w-4 h-4" />
                      <span>Input</span>
                      <span className="text-blue-400">→</span>
                      <span>Event Extraction</span>
                      <span className="text-blue-400">→</span>
                      <span>{batchResult.processed} Events</span>
                      <span className="text-blue-400">→</span>
                      <span>Per-Event Detection + Parsing</span>
                      <span className="text-blue-400">→</span>
                      <span>Normalization</span>
                      <span className="text-blue-400">→</span>
                      <span>Validation</span>
                      <span className="text-blue-400">→</span>
                      <span className="font-bold">Results</span>
                    </div>
                  </div>
                )}

                <div className={!batchResult ? "mt-8 border-t border-slate-100 pt-8" : ""}>
                  {error ? (
                    <div className="bg-red-50 p-6 rounded-xl border border-red-200">
                      <div className="flex items-center gap-2 mb-2">
                        <XCircle className="w-6 h-6 text-red-600" />
                        <h3 className="text-lg font-bold text-red-900">Processing Error</h3>
                      </div>
                      <p className="text-sm text-red-700 font-mono">{error}</p>
                    </div>
                  ) : batchResult ? (
                    <BatchResultView batchResult={batchResult} onPluginConfirmed={handlePluginConfirmed} />
                  ) : result ? (
                    <ResultView result={result} onPluginConfirmed={handlePluginConfirmed} />
                  ) : (
                    <div className="text-center text-slate-400 py-12 animate-pulse">
                      Analyzing and processing log event...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* PLUGIN REGISTRY */}
        {activeView === 'plugins' && <PluginRegistry />}

        {/* HISTORY */}
        {activeView === 'history' && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary-600" /> Processing History
              </h2>
              {history.length > 0 && (
                <button
                  onClick={() => { setHistory([]); localStorage.removeItem('ulpf_history'); }}
                  className="text-xs text-red-500 hover:text-red-700 font-medium border border-red-200 px-3 py-1 rounded-lg"
                >
                  Clear History
                </button>
              )}
            </div>
            {history.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 text-sm border-b border-slate-200">
                      <th className="p-3 font-semibold">Timestamp</th>
                      <th className="p-3 font-semibold">Format</th>
                      <th className="p-3 font-semibold">Validation</th>
                      <th className="p-3 font-semibold">Confidence</th>
                      <th className="p-3 font-semibold">Source</th>
                      <th className="p-3 font-semibold">Raw Preview</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr
                        key={item.id}
                        className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => handleReplay(item)}
                      >
                        <td className="p-3 text-sm text-slate-600 whitespace-nowrap">{item.timestamp}</td>
                        <td className="p-3 text-sm font-medium text-slate-800">{item.format}</td>
                        <td className="p-3 text-sm">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${item.validation === 'VALID' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            {item.validation}
                          </span>
                        </td>
                        <td className="p-3 text-sm text-slate-600">{((item.confidence || 0) * 100).toFixed(1)}%</td>
                        <td className="p-3 text-sm text-slate-500">{item.source_file || '—'}</td>
                        <td className="p-3 text-sm text-slate-400 font-mono truncate max-w-xs">{item.raw}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-400">
                <Clock className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No processing history yet.</p>
                <button onClick={() => setActiveView('process')} className="mt-3 text-primary-600 hover:underline text-sm">
                  Go to Process Log →
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
