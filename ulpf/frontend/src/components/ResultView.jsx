import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, Copy, Puzzle, CheckSquare, Sparkles, Zap, RotateCcw } from 'lucide-react';
import { confirmPlugin } from '../api/client';

const SummaryCard = ({ label, value, subtext, status }) => (
  <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
    <div className="text-xs text-slate-500 font-semibold mb-1 uppercase tracking-wider">{label}</div>
    <div className="text-lg font-bold text-slate-800 flex items-center gap-2">
      {status === 'success' && <CheckCircle className="w-5 h-5 text-green-500" />}
      {status === 'warning' && <AlertTriangle className="w-5 h-5 text-orange-500" />}
      {status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
      {status === 'plugin' && <Puzzle className="w-5 h-5 text-purple-500" />}
      {value}
    </div>
    {subtext && <div className="text-xs text-slate-400 mt-1">{subtext}</div>}
  </div>
);

// Canonical list of target fields from ULPF UniversalEvent schema
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

const ConfirmMappingPanel = ({ result, onPluginConfirmed }) => {
  const [pluginName, setPluginName] = useState('Custom Plugin');
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');

  const structure = result.structure || {};
  const delimiter = structure.delimiter || '|';
  const fieldCount = structure.fields || 0;
  const formatType = structure.format_type || 'delimited';
  const lineCount = structure.line_count || 1;
  const prefixPattern = structure.prefix_pattern || null;
  const fieldTypes = structure.data_types || [];
  const candidateMappings = result.candidate_mappings || {};

  // Build initial mappings from candidate_mappings
  const getInitialMappings = () => {
    const init = {};
    Object.entries(candidateMappings).forEach(([fieldKey, info]) => {
      init[fieldKey] = info.mapped_to || '';
    });
    return init;
  };

  const [userMappings, setUserMappings] = useState(getInitialMappings);

  useEffect(() => {
    setUserMappings(getInitialMappings());
  }, [result]);

  const handleMappingChange = (fieldKey, selectedTarget) => {
    setUserMappings(prev => ({
      ...prev,
      [fieldKey]: selectedTarget
    }));
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError('');
    try {
      const signature = { 
        format_type: formatType,
        delimiter, 
        field_count: fieldCount, 
        line_count: lineCount,
        prefix_pattern: prefixPattern,
        field_types: fieldTypes 
      };

      // Build final field_mappings using user's explicit selections
      const finalFieldMappings = {};
      Object.entries(userMappings).forEach(([fieldKey, targetField]) => {
        if (targetField && targetField.trim()) {
          finalFieldMappings[fieldKey] = targetField.trim();
        }
      });

      const res = await confirmPlugin(pluginName, signature, finalFieldMappings);
      if (res.status === 'success') {
        setConfirmed(true);
        if (onPluginConfirmed) onPluginConfirmed(res.plugin);
      } else {
        setError(res.message || 'Failed to confirm plugin.');
      }
    } catch (e) {
      setError(e.message || 'Error communicating with backend.');
    } finally {
      setConfirming(false);
    }
  };

  if (confirmed) {
    return (
      <div className="mt-4 flex items-center gap-3 bg-green-50 border border-green-200 rounded-xl p-4 text-green-800">
        <CheckSquare className="w-6 h-6 text-green-600 flex-shrink-0" />
        <div>
          <div className="font-bold">Plugin Created Successfully</div>
          <div className="text-sm">Future events matching this structure will be parsed automatically without Groq API calls.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-xl p-5">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-bold text-indigo-900 flex items-center gap-2 text-base">
            <Sparkles className="w-5 h-5 text-violet-600" />
            AI Schema Discovery
          </h4>
          <p className="text-xs text-indigo-700 mt-1">
            {result?.ai_status === 'fallback' || structure.structure_source === 'regex'
              ? 'AI mapping unavailable — fallback structure analysis used. Review and define field mappings manually.'
              : 'AI Suggested Mapping — Review and modify the suggested mappings before creating the plugin.'}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {structure.structure_source === 'groq' || result?.ai_status === 'success' ? (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
              <Zap className="w-3 h-3 text-emerald-600" /> AI Discovered (Groq)
            </span>
          ) : (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
              Regex Fallback
            </span>
          )}
          {result?.confidence?.mapping && (
            <span className="text-[11px] font-medium text-indigo-600">
              Confidence: {(result.confidence.mapping * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 mb-1">Plugin Name</label>
        <input
          type="text"
          value={pluginName}
          onChange={e => setPluginName(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 bg-white"
          placeholder="e.g. Custom Firewall Log Plugin"
        />
      </div>

      <div className="mb-4 text-xs text-slate-600 flex flex-wrap gap-4 bg-white p-2.5 rounded-lg border border-slate-200">
        <div><span className="font-semibold text-slate-700">Format:</span> <code className="bg-slate-100 px-1.5 py-0.5 rounded">{formatType}</code></div>
        <div><span className="font-semibold text-slate-700">Delimiter:</span> <code className="bg-slate-100 px-1.5 py-0.5 rounded">{delimiter === null ? 'None' : delimiter === '\t' ? '\\t (tab)' : delimiter}</code></div>
        <div><span className="font-semibold text-slate-700">Field Count:</span> {fieldCount}</div>
      </div>

      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-700 mb-2">Editable Field Mappings:</div>
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden text-sm">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <th className="px-3 py-2">Source Field</th>
                <th className="px-3 py-2">Sample Value</th>
                <th className="px-3 py-2">Target Universal Schema Field</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(candidateMappings).map(([fieldKey, info], i) => (
                <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-slate-600">{fieldKey}</td>
                  <td className="px-3 py-2 font-mono text-slate-800 max-w-[200px] truncate" title={info.value}>{info.value}</td>
                  <td className="px-3 py-2">
                    <select
                      value={userMappings[fieldKey] || ''}
                      onChange={e => handleMappingChange(fieldKey, e.target.value)}
                      className="w-full px-2 py-1.5 border border-slate-300 rounded text-sm bg-white font-mono text-indigo-700 font-semibold focus:ring-2 focus:ring-indigo-400 cursor-pointer"
                    >
                      <option value="">-- Unmapped (Ignore) --</option>
                      {CANONICAL_TARGET_FIELDS.map(tf => (
                        <option key={tf} value={tf}>{tf}</option>
                      ))}
                    </select>
                    {info.ai_reason && (
                      <div className="text-xs text-slate-400 mt-0.5 italic">{info.ai_reason}</div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && (
        <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleConfirm}
          disabled={confirming || !pluginName.trim()}
          className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold rounded-lg text-sm transition-colors"
        >
          {confirming ? (
            <><span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /><span>Saving Plugin...</span></>
          ) : (
            <><CheckSquare className="w-4 h-4" /><span>Create Plugin From Mapping</span></>
          )}
        </button>
        <button
          type="button"
          onClick={() => setUserMappings(getInitialMappings())}
          className="flex items-center gap-1.5 px-4 py-2 border border-slate-300 text-slate-600 rounded-lg text-sm hover:bg-slate-100 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset AI Mapping</span>
        </button>
      </div>
    </div>
  );
};

const ResultView = ({ result, onPluginConfirmed }) => {
  const [activeTab, setActiveTab] = useState('universal');

  if (!result || result.status === 'not implemented') {
    return (
      <div className="bg-orange-50 p-6 rounded-xl border border-orange-200 text-center">
        <AlertTriangle className="w-8 h-8 text-orange-500 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-orange-800">Endpoint Not Implemented</h3>
        <p className="text-sm text-orange-600 mt-2">
          The backend API returned a "not implemented" status.
        </p>
      </div>
    );
  }

  const detectedFormat = result?.detected_format || 'Unknown';
  const confidence = typeof result?.confidence?.overall === 'number'
    ? (result.confidence.overall * 100).toFixed(1)
    : 'N/A';
  const validationStatus = result?.validation?.status || 'UNKNOWN';
  const isUnknown = detectedFormat === 'UNKNOWN';
  const isCustomPlugin = detectedFormat === 'CUSTOM_PLUGIN';
  const isQuarantined = validationStatus !== 'VALID';

  const statusStatus = isQuarantined ? 'error' : 'success';
  const formatStatus = isUnknown ? 'warning' : isCustomPlugin ? 'plugin' : 'success';

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Source file badge */}
      {result.source_file && (
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
          <Info className="w-4 h-4 text-slate-400" />
          Source file: <span className="font-semibold text-slate-700">{result.source_file}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard label="Format" value={detectedFormat} status={formatStatus} />
        <SummaryCard label="Parser" value={result.parser || 'N/A'} />
        <SummaryCard
          label="Confidence"
          value={confidence === 'N/A' ? 'N/A' : confidence + '%'}
          status={parseFloat(confidence) > 80 ? 'success' : 'warning'}
        />
        <SummaryCard label="Validation" value={validationStatus} status={statusStatus} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="flex border-b border-slate-200 overflow-x-auto">
          {['universal', 'internal', 'unmapped', 'raw', 'traceability'].map(tab => {
            const labels = {
              universal:    'Universal Event',
              internal:     'Normalized Event',
              unmapped:     'Unmapped Fields',
              raw:          'Raw Event',
              traceability: 'Traceability',
            };
            return (
              <button
                key={tab}
                className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                  activeTab === tab
                    ? tab === 'universal'
                      ? 'border-emerald-500 text-emerald-700 bg-emerald-50'
                      : 'border-primary-500 text-primary-600 bg-primary-50'
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'universal' ? (
                  <span className="flex items-center gap-1.5">
                    {labels[tab]}
                    <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">OCSF</span>
                  </span>
                ) : labels[tab]}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {/* ── UNIVERSAL EVENT (OCSF) ── */}
          {activeTab === 'universal' && (
            <div>
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold text-slate-800">Universal Event</h3>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">OCSF v{result.ocsf?.metadata?.version || '1.3.0'}</span>
                  <span className="text-xs font-semibold text-slate-500">{result.ocsf?.class_name || 'Network Activity'}</span>
                  {result.ocsf_validation?.status === 'VALID' ? (
                    <span className="flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                      <CheckCircle className="w-3 h-3" /> VALID
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700">
                      <AlertTriangle className="w-3 h-3" /> INVALID
                    </span>
                  )}
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(result.ocsf || {}, null, 2))}
                  className="flex items-center space-x-1 text-sm text-slate-500 hover:text-primary-600"
                >
                  <Copy className="w-4 h-4" /><span>Copy JSON</span>
                </button>
              </div>

              <div className="mb-3 flex items-center gap-6 text-xs text-slate-500 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2">
                <span><span className="font-semibold text-emerald-700">Standard:</span> Open Cybersecurity Schema Framework</span>
                <span><span className="font-semibold text-emerald-700">Class UID:</span> {result.ocsf?.class_uid ?? 4001}</span>
                <span><span className="font-semibold text-emerald-700">Category:</span> {result.ocsf?.category_name || 'Network Activity'}</span>
              </div>

              {result.ocsf_validation?.status === 'INVALID' && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  <span className="font-bold">OCSF Validation Errors:</span>
                  <ul className="list-disc pl-5 mt-1">
                    {result.ocsf_validation.errors?.map((err, i) => <li key={i}>{err}</li>)}
                  </ul>
                </div>
              )}

              <div className="bg-slate-900 text-emerald-300 rounded-lg border border-slate-700 p-4 font-mono text-sm overflow-x-auto">
                <pre>{JSON.stringify(result.ocsf || {}, null, 2)}</pre>
              </div>

              <p className="mt-3 text-xs text-slate-400 italic">
                This is the final standardized Universal Event — produced by the OCSF Mapper from the internal normalized representation. Downstream SIEM, Data Lake, and AI systems consume this.
              </p>
            </div>
          )}

          {/* ── NORMALIZED EVENT (Internal) ── */}
          {activeTab === 'internal' && (
            <div>
              <div className="flex justify-between items-center mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">Normalized Event</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Internal normalized representation — ULPF Universal Semantic Model</p>
                </div>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(result.normalized_event || {}, null, 2))}
                  className="flex items-center space-x-1 text-sm text-slate-500 hover:text-primary-600"
                >
                  <Copy className="w-4 h-4" /><span>Copy JSON</span>
                </button>
              </div>
              <div className="mb-3 flex items-center gap-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2">
                <Info className="w-3.5 h-3.5 flex-shrink-0" />
                Intermediate representation produced by <code className="font-mono bg-white border border-slate-200 rounded px-1">normalize_event()</code>. Format-agnostic; feeds the OCSF Mapper.
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
                <div className="flex flex-wrap gap-4">
                  {Object.entries(result.provenance).map(([key, prov]) => (
                    <div key={key} className="flex flex-col items-center text-sm font-mono bg-slate-50 p-4 rounded-lg border border-slate-200 w-full sm:w-64 flex-shrink-0">
                      <span className="text-primary-600 font-bold">{key}</span>
                      <span className="text-slate-400 my-1">↓</span>
                      <span className="text-slate-600 font-medium">{prov.original_field}</span>
                      <span className="text-slate-400 my-1">↓</span>
                      <span className="text-slate-800 font-bold truncate max-w-full" title={prov.original_value}>{prov.original_value}</span>
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

      {/* Validation / Quarantine Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 bg-slate-50">
          <h3 className="text-lg font-semibold text-slate-800">Data Quality &amp; Validation</h3>
        </div>
        <div className="p-6">
          {validationStatus === 'VALID' ? (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">All fields passed schema validation.</span>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-red-600 font-bold border-b border-red-100 pb-2">
                <AlertTriangle className="w-6 h-6" />
                <span className="text-lg">⚠ EVENT QUARANTINED</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-700 bg-red-50 p-4 rounded-lg border border-red-200 shadow-sm">
                <div>
                  <p className="mb-2"><span className="font-semibold">Status:</span> <span className="text-red-700 font-bold">QUARANTINED</span></p>
                  <p className="mb-2"><span className="font-semibold">Reason:</span> Validation failed</p>
                  {result.event_id && <p className="text-xs text-slate-500">Event ID: {result.event_id}</p>}
                </div>
                <div>
                  <span className="font-semibold block mb-1">Validation Errors:</span>
                  <ul className="list-disc pl-5 text-red-800">
                    {result?.validation?.errors?.map((err, i) => (
                      <li key={i}><span className="font-semibold">{err.field}:</span> {err.message}</li>
                    )) || <li>Unknown validation error occurred.</li>}
                  </ul>
                </div>
              </div>
              <div className="text-sm font-medium text-slate-600 flex items-center bg-slate-50 p-3 rounded-lg border border-slate-200">
                <Info className="w-5 h-5 text-blue-500 mr-2" />
                Original event preserved for forensic traceability. View in Raw Event tab.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Unknown Format — Adaptive Intelligence + Editable Confirm Mapping */}
      {isUnknown && result?.confidence && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-100 bg-indigo-50">
            <h3 className="text-lg font-semibold text-indigo-900 flex items-center gap-2">
              <Info className="w-5 h-5 text-indigo-600" />
              Adaptive Intelligence: Structure Analysis
              {result.ai_used && (
                <span className="ml-auto flex items-center gap-1.5 text-xs font-semibold bg-violet-100 text-violet-700 border border-violet-200 px-2.5 py-1 rounded-full">
                  <Sparkles className="w-3.5 h-3.5" /> AI Assisted
                </span>
              )}
              {result.ai_status === 'unavailable' && (
                <span className="ml-auto flex items-center gap-1.5 text-xs font-semibold bg-orange-100 text-orange-700 border border-orange-200 px-2.5 py-1 rounded-full">
                  <Zap className="w-3.5 h-3.5" /> AI Unavailable
                </span>
              )}
            </h3>
          </div>
          <div className="p-6">
            <ConfirmMappingPanel result={result} onPluginConfirmed={onPluginConfirmed} />
          </div>
        </div>
      )}

      {/* Custom Plugin recognized */}
      {isCustomPlugin && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5 flex items-center gap-4">
          <Puzzle className="w-8 h-8 text-purple-500 flex-shrink-0" />
          <div>
            <div className="font-bold text-purple-900">Custom Plugin Recognized</div>
            <div className="text-sm text-purple-700">This event matched a stored plugin: <strong>{result.parser}</strong>. Processed automatically without Groq API calls.</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultView;
