import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, Copy, Puzzle, CheckSquare } from 'lucide-react';
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

const ConfirmMappingPanel = ({ result, onPluginConfirmed }) => {
  const [pluginName, setPluginName] = useState('Custom Plugin');
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');

  // Build signature and field_mappings from provenance / unmapped_fields
  const structure = result._structure || {};
  const delimiter = structure.delimiter || '|';
  const fieldCount = structure.field_count || 0;
  const fieldTypes = structure.field_types || [];
  const candidateMappings = result._candidate_mappings || {};

  const fieldMappings = {};
  let idx = 0;
  Object.entries(candidateMappings).forEach(([fieldKey, info]) => {
    if (info.mapped_to) {
      fieldMappings[String(idx)] = info.mapped_to;
    }
    idx++;
  });

  const handleConfirm = async () => {
    setConfirming(true);
    setError('');
    try {
      const signature = { delimiter, field_count: fieldCount, field_types: fieldTypes };
      const res = await confirmPlugin(pluginName, signature, fieldMappings);
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
          <div className="text-sm">Future events matching this structure will be parsed automatically.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 bg-indigo-50 border border-indigo-200 rounded-xl p-5">
      <h4 className="font-bold text-indigo-900 mb-3 flex items-center gap-2">
        <Puzzle className="w-5 h-5" />
        Create Plugin from This Format
      </h4>

      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-700 mb-1">Plugin Name</label>
        <input
          type="text"
          value={pluginName}
          onChange={e => setPluginName(e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 bg-white"
        />
      </div>

      <div className="mb-4 text-sm text-slate-600 space-y-1">
        <div><span className="font-semibold">Delimiter:</span> <code className="bg-white px-2 py-0.5 rounded border border-slate-200">{delimiter === '\t' ? '\\t (tab)' : delimiter}</code></div>
        <div><span className="font-semibold">Fields:</span> {fieldCount}</div>
      </div>

      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-700 mb-2">Confirmed Field Mappings:</div>
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden text-sm">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <th className="text-left px-3 py-2">Index</th>
                <th className="text-left px-3 py-2">Field Value</th>
                <th className="text-left px-3 py-2">Maps To</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(candidateMappings).map(([fieldKey, info], i) => (
                <tr key={i} className="border-b border-slate-100 last:border-0">
                  <td className="px-3 py-2 text-slate-500 font-mono">{i}</td>
                  <td className="px-3 py-2 font-mono">{info.value}</td>
                  <td className="px-3 py-2">
                    {info.mapped_to
                      ? <span className="text-indigo-600 font-semibold">{info.mapped_to}</span>
                      : <span className="text-slate-400 italic">unmapped</span>}
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
          onClick={handleConfirm}
          disabled={confirming || !pluginName.trim()}
          className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-semibold rounded-lg text-sm transition-colors"
        >
          {confirming ? (
            <><span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /><span>Saving...</span></>
          ) : (
            <><CheckSquare className="w-4 h-4" /><span>Confirm Mapping</span></>
          )}
        </button>
        <button className="px-5 py-2 border border-slate-300 text-slate-600 rounded-lg text-sm hover:bg-slate-50 transition-colors">
          Reject / Review
        </button>
      </div>
    </div>
  );
};

const ResultView = ({ result, onPluginConfirmed }) => {
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
          {['normalized', 'unmapped', 'raw', 'traceability'].map(tab => (
            <button
              key={tab}
              className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${activeTab === tab ? 'border-primary-500 text-primary-600 bg-primary-50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'normalized' ? 'Universal Event' : tab === 'unmapped' ? 'Unmapped Fields' : tab === 'raw' ? 'Raw Event' : 'Traceability'}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'normalized' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-800">Normalized Fields</h3>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(result.normalized_event || {}, null, 2))}
                  className="flex items-center space-x-1 text-sm text-slate-500 hover:text-primary-600"
                >
                  <Copy className="w-4 h-4" /><span>Copy JSON</span>
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

      {/* Unknown Format — Adaptive Intelligence + Confirm Mapping */}
      {isUnknown && result?.confidence && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-6 border-b border-slate-100 bg-indigo-50">
            <h3 className="text-lg font-semibold text-indigo-900 flex items-center gap-2">
              <Info className="w-5 h-5 text-indigo-600" />
              Adaptive Intelligence: Structure Analysis
            </h3>
          </div>
          <div className="p-6">
            <div className="mb-4">
              <span className="font-semibold text-slate-700">Confidence Score:</span>{' '}
              {(result.confidence.mapping * 100).toFixed(1)}%
            </div>

            <h4 className="font-semibold text-slate-700 mb-2">Candidate Field Mappings</h4>
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 font-mono text-sm overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-200">
                    <th className="pb-2">Field</th>
                    <th className="pb-2">Value</th>
                    <th className="pb-2">Mapped To</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.provenance || {}).map(([key, prov], i) => (
                    <tr key={i} className="border-b border-slate-100 last:border-0">
                      <td className="py-2 text-slate-600">{prov.original_field}</td>
                      <td className="py-2">{prov.original_value}</td>
                      <td className="py-2 text-indigo-600 font-semibold">→ {key}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {result.confidence.human_review_required && (
              <div className="mt-4 flex items-center space-x-2 text-orange-600 bg-orange-50 p-3 rounded-lg border border-orange-200">
                <AlertTriangle className="w-5 h-5" />
                <span className="text-sm font-medium">⚠ Human Review Recommended due to low confidence or unmapped fields.</span>
              </div>
            )}

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
            <div className="text-sm text-purple-700">This event matched a stored plugin: <strong>{result.parser}</strong>. Processed automatically without human intervention.</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultView;
