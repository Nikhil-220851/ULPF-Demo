import React, { useState, useEffect } from 'react';
import { Puzzle, RefreshCw, CheckCircle, XCircle, Eye } from 'lucide-react';
import { getPlugins } from '../api/client';

const PluginRegistry = () => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(null);

  const fetchPlugins = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getPlugins();
      setPlugins(data);
    } catch (e) {
      setError('Failed to load plugins: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPlugins(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Puzzle className="w-6 h-6 text-purple-600" />
            Plugin Registry
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Custom format plugins created from human-confirmed unknown events. Future matching events are parsed automatically.
          </p>
        </div>
        <button
          onClick={fetchPlugins}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && !error && plugins.length === 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-16 text-center text-slate-400">
          <Puzzle className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="font-medium">No plugins yet.</p>
          <p className="text-sm mt-1">Process an unknown format event and confirm the mapping to create your first plugin.</p>
        </div>
      )}

      {plugins.length > 0 && (
        <div className="space-y-3">
          {plugins.map(plugin => (
            <div key={plugin.plugin_id} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Puzzle className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-800">{plugin.name}</div>
                    <div className="text-xs text-slate-500 font-mono">{plugin.plugin_id}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="hidden md:flex items-center gap-2 text-xs text-slate-600">
                    <span className="bg-slate-100 px-2 py-0.5 rounded font-mono">
                      delim: "{plugin.signature?.delimiter === '\t' ? '\\t' : plugin.signature?.delimiter}"
                    </span>
                    <span className="bg-slate-100 px-2 py-0.5 rounded font-mono">
                      {plugin.signature?.field_count} fields
                    </span>
                  </div>
                  {plugin.enabled
                    ? <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-bold rounded-full bg-green-100 text-green-700"><CheckCircle className="w-3 h-3" />ACTIVE</span>
                    : <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-bold rounded-full bg-slate-100 text-slate-500"><XCircle className="w-3 h-3" />DISABLED</span>
                  }
                  <button
                    onClick={() => setExpanded(expanded === plugin.plugin_id ? null : plugin.plugin_id)}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-slate-600"
                  >
                    <Eye className="w-3 h-3" />
                    {expanded === plugin.plugin_id ? 'Hide' : 'View'}
                  </button>
                </div>
              </div>

              {expanded === plugin.plugin_id && (
                <div className="border-t border-slate-100 p-5 bg-slate-50 space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500 block mb-1">Version</span>
                      <span className="font-semibold">{plugin.version || '1.0'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-1">Created By</span>
                      <span className="font-semibold">{plugin.created_by}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-1">Confidence</span>
                      <span className="font-semibold">{((plugin.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block mb-1">Delimiter</span>
                      <code className="bg-white px-2 py-0.5 rounded border border-slate-200 font-mono">
                        {plugin.signature?.delimiter === '\t' ? '\\t (tab)' : plugin.signature?.delimiter}
                      </code>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-slate-700 mb-2">Field Mappings</div>
                    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden text-sm">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-slate-50 text-slate-500 border-b border-slate-200">
                            <th className="text-left px-3 py-2">Index</th>
                            <th className="text-left px-3 py-2">Maps To</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(plugin.field_mappings || {}).map(([idx, mapped]) => (
                            <tr key={idx} className="border-b border-slate-100 last:border-0">
                              <td className="px-3 py-2 font-mono text-slate-500">Field {idx}</td>
                              <td className="px-3 py-2 text-purple-700 font-semibold">{mapped}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-semibold text-slate-700 mb-1">Format Signature (JSON)</div>
                    <pre className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs overflow-x-auto">
                      {JSON.stringify(plugin.signature, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PluginRegistry;
