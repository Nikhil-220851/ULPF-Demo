import React, { useState, useEffect } from 'react';
import { Puzzle, RefreshCw, CheckCircle, XCircle, Eye, Plus, Trash2, Edit3, X, AlertTriangle } from 'lucide-react';
import { getPlugins, deletePlugin, confirmPlugin, updatePlugin } from '../api/client';

const CANONICAL_TARGET_FIELDS = [
  'event.timestamp',
  'event.action',
  'event.outcome',
  'event.message',
  'event.application',
  'event.category',
  'event.type',
  'event.id',
  'source.ip',
  'source.port',
  'source.hostname',
  'source.domain',
  'source.mac',
  'source.user',
  'destination.ip',
  'destination.port',
  'destination.hostname',
  'destination.domain',
  'destination.mac',
  'network.protocol',
  'network.direction',
  'network.bytes',
  'network.packets',
  'network.transport',
  'user.name',
  'user.id',
  'user.domain',
  'user.email',
  'device.hostname',
  'device.ip',
  'device.mac',
  'device.type',
  'device.os',
  'device.vendor',
  'severity',
];

const PluginRegistry = () => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(null);

  // Create plugin modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPluginName, setNewPluginName] = useState('');
  const [newDelimiter, setNewDelimiter] = useState('::');
  const [newFieldCount, setNewFieldCount] = useState(6);
  const [newMappings, setNewMappings] = useState({
    field_1: 'device.hostname',
    field_2: 'event.timestamp',
    field_3: 'source.ip',
    field_4: 'destination.ip',
    field_5: 'network.transport',
    field_6: 'event.action'
  });

  // Delete modal state
  const [deletingPlugin, setDeletingPlugin] = useState(null);
  const [deleting, setDeleting] = useState(false);

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

  const handleDelete = async () => {
    if (!deletingPlugin) return;
    setDeleting(true);
    try {
      await deletePlugin(deletingPlugin.plugin_id);
      setDeletingPlugin(null);
      await fetchPlugins();
    } catch (e) {
      setError('Failed to delete plugin: ' + e.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleCreatePlugin = async (e) => {
    e.preventDefault();
    if (!newPluginName.trim()) return;

    try {
      const signature = {
        format_type: 'delimited',
        delimiter: newDelimiter,
        field_count: Number(newFieldCount),
        line_count: 1,
        prefix_pattern: null
      };

      const res = await confirmPlugin(newPluginName, signature, newMappings);
      if (res.status === 'success') {
        setShowCreateModal(false);
        setNewPluginName('');
        await fetchPlugins();
      } else {
        setError(res.message || 'Failed to create plugin.');
      }
    } catch (err) {
      setError('Error creating plugin: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Puzzle className="w-6 h-6 text-purple-600" />
            Plugin Registry
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Custom format plugins created from human-confirmed unknown events. Future matching events are parsed automatically without Groq API calls.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Create Plugin
          </button>
          <button
            onClick={fetchPlugins}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
      )}

      {!loading && !error && plugins.length === 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-16 text-center text-slate-400">
          <Puzzle className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="font-medium">No plugins yet.</p>
          <p className="text-sm mt-1">Process an unknown format event and confirm the mapping to create your first plugin, or click "+ Create Plugin" above.</p>
        </div>
      )}

      {plugins.length > 0 && (
        <div className="space-y-3">
          {plugins.map(plugin => (
            <div key={plugin.plugin_id} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="flex items-center justify-between px-5 py-4 flex-wrap gap-3">
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
                  <button
                    onClick={() => setDeletingPlugin(plugin)}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs border border-red-200 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
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
                      <table className="w-full text-left">
                        <thead>
                          <tr className="bg-slate-50 text-slate-500 border-b border-slate-200">
                            <th className="px-3 py-2">Source Field</th>
                            <th className="px-3 py-2">Maps To Target Field</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(plugin.field_mappings || {}).map(([idx, mapped]) => (
                            <tr key={idx} className="border-b border-slate-100 last:border-0">
                              <td className="px-3 py-2 font-mono text-slate-600">{idx}</td>
                              <td className="px-3 py-2 text-purple-700 font-semibold font-mono">{mapped}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingPlugin && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center gap-3 text-red-600 mb-3">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <h3 className="text-lg font-bold text-slate-900">Delete Plugin?</h3>
            </div>
            <p className="text-sm text-slate-600 mb-4">
              Are you sure you want to delete <strong className="text-slate-800">{deletingPlugin.name}</strong>? Subsequent matching events will no longer be parsed by this plugin.
            </p>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDeletingPlugin(null)}
                disabled={deleting}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Plugin Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Plus className="w-5 h-5 text-purple-600" />
                Create Format Plugin
              </h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePlugin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Plugin Name</label>
                <input
                  type="text"
                  required
                  value={newPluginName}
                  onChange={e => setNewPluginName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                  placeholder="e.g. Custom Firewall Format"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Delimiter</label>
                  <input
                    type="text"
                    required
                    value={newDelimiter}
                    onChange={e => setNewDelimiter(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono bg-white"
                    placeholder="e.g. :: or |"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Field Count</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={newFieldCount}
                    onChange={e => setNewFieldCount(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-2">Field Target Mappings</label>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {Array.from({ length: Number(newFieldCount) || 1 }).map((_, idx) => {
                    const key = `field_${idx + 1}`;
                    return (
                      <div key={key} className="flex items-center gap-2 text-xs">
                        <span className="font-mono text-slate-600 w-16 flex-shrink-0">{key}:</span>
                        <select
                          value={newMappings[key] || ''}
                          onChange={e => setNewMappings(prev => ({ ...prev, [key]: e.target.value }))}
                          className="w-full px-2 py-1.5 border border-slate-300 rounded text-xs font-mono bg-white text-purple-700 font-semibold"
                        >
                          <option value="">-- Unmapped --</option>
                          {CANONICAL_TARGET_FIELDS.map(tf => (
                            <option key={tf} value={tf}>{tf}</option>
                          ))}
                        </select>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold transition-colors"
                >
                  Create Plugin
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PluginRegistry;
