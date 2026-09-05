import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, ChevronDown, ChevronRight, Puzzle, FileText } from 'lucide-react';
import ResultView from './ResultView';

const statusBadge = (status) => {
  if (status === 'VALID') return <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-green-100 text-green-700">VALID</span>;
  if (status === 'QUARANTINED') return <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-orange-100 text-orange-700">QUARANTINED</span>;
  if (status === 'ERROR') return <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-red-100 text-red-700">ERROR</span>;
  return <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-red-100 text-red-700">{status || 'INVALID'}</span>;
};

const formatBadge = (format) => {
  const colors = {
    SYSLOG: 'bg-blue-100 text-blue-700',
    JSON: 'bg-yellow-100 text-yellow-700',
    CEF: 'bg-green-100 text-green-700',
    LEEF: 'bg-teal-100 text-teal-700',
    KEYVALUE: 'bg-violet-100 text-violet-700',
    CSV: 'bg-pink-100 text-pink-700',
    CUSTOM_PLUGIN: 'bg-purple-100 text-purple-700',
    UNKNOWN: 'bg-slate-100 text-slate-600',
  };
  const cls = colors[format] || 'bg-slate-100 text-slate-600';
  return <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${cls}`}>{format}</span>;
};

const EventRow = ({ index, result, onPluginConfirmed }) => {
  const [expanded, setExpanded] = useState(false);
  const validationStatus = result?.validation?.status || 'UNKNOWN';
  const isQuarantined = validationStatus !== 'VALID';
  const isCustomPlugin = result?.detected_format === 'CUSTOM_PLUGIN';

  return (
    <div className={`border rounded-xl overflow-hidden ${isQuarantined ? 'border-red-200' : isCustomPlugin ? 'border-purple-200' : 'border-slate-200'}`}>
      <button
        className={`w-full flex items-center justify-between px-5 py-4 text-left transition-colors ${isQuarantined ? 'bg-red-50 hover:bg-red-100' : isCustomPlugin ? 'bg-purple-50 hover:bg-purple-100' : 'bg-slate-50 hover:bg-slate-100'}`}
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-3 min-w-0">
          {isQuarantined
            ? <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
            : isCustomPlugin
              ? <Puzzle className="w-5 h-5 text-purple-500 flex-shrink-0" />
              : <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
          <span className="font-semibold text-slate-700 flex-shrink-0">Event #{index + 1}</span>
          {result.source_file && (
            <span className="flex items-center gap-1 text-xs text-slate-400 hidden sm:inline-flex">
              <FileText className="w-3 h-3" />
              {result.source_file}
            </span>
          )}
          <span className="text-xs text-slate-400 font-mono truncate max-w-xs hidden md:inline">
            {result.raw_event?.slice(0, 60)}{result.raw_event?.length > 60 ? '…' : ''}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {formatBadge(result.detected_format)}
          {result.parser && (
            <span className="text-xs font-medium text-slate-600 border border-slate-200 px-2 py-0.5 rounded hidden lg:inline">
              {result.parser}
            </span>
          )}
          {statusBadge(validationStatus)}
          <span className="text-xs text-slate-500">
            {result.confidence?.overall != null ? `${(result.confidence.overall * 100).toFixed(0)}%` : ''}
          </span>
          {expanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {expanded && (
        <div className="p-5 border-t border-slate-200 bg-white">
          <ResultView result={result} onPluginConfirmed={onPluginConfirmed} />
        </div>
      )}
    </div>
  );
};

const QuarantineReportButton = ({ results }) => {
  const quarantined = results.filter(r => r.validation?.status !== 'VALID');
  if (quarantined.length === 0) return null;

  const handleGenerate = () => {
    const report = {
      report_id: 'RPT-' + Date.now(),
      generated_at: new Date().toISOString(),
      summary: {
        total_events: results.length,
        quarantined_events: quarantined.length,
        valid_events: results.length - quarantined.length,
      },
      quarantined_events: quarantined.map(r => ({
        event_id: r.event_id,
        source_file: r.source_file || null,
        source_file_index: r.source_file_index ?? null,
        detected_format: r.detected_format,
        parser: r.parser,
        validation_status: r.validation?.status,
        quarantine_reason: 'Validation failed',
        validation_errors: r.validation?.errors || [],
        validation_warnings: r.validation?.warnings || [],
        raw_event: r.raw_event,
        normalized_event: r.normalized_event,
        unmapped_fields: r.unmapped_fields,
        provenance: r.provenance,
        confidence: r.confidence,
      })),
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ulpf-quarantine-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      onClick={handleGenerate}
      className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
    >
      <XCircle className="w-4 h-4" />
      Generate Quarantine Report ({quarantined.length})
    </button>
  );
};

const BatchResultView = ({ batchResult, onPluginConfirmed }) => {
  if (!batchResult) return null;

  const { total, processed, results } = batchResult;
  const validCount = results.filter(r => r.validation?.status === 'VALID').length;
  const quarantinedCount = results.filter(r => r.validation?.status !== 'VALID').length;
  const unknownCount = results.filter(r => r.detected_format === 'UNKNOWN').length;
  const customPluginCount = results.filter(r => r.detected_format === 'CUSTOM_PLUGIN').length;
  const sourceFiles = [...new Set(results.map(r => r.source_file).filter(Boolean))];

  return (
    <div className="space-y-6">
      {/* Summary bar */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <Info className="w-5 h-5 text-primary-600" />
            Batch Processing Summary
          </h3>
          <QuarantineReportButton results={results} />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {sourceFiles.length > 0 && (
            <div className="text-center col-span-1">
              <p className="text-2xl font-bold text-slate-600">{sourceFiles.length}</p>
              <p className="text-xs text-slate-500 mt-1 font-medium uppercase tracking-wider">Files</p>
            </div>
          )}
          <div className="text-center">
            <p className="text-3xl font-bold text-slate-800">{total}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium uppercase tracking-wider">Total Events</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-slate-800">{processed}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium uppercase tracking-wider">Processed</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-bold text-green-600">{validCount}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium uppercase tracking-wider">Valid</p>
          </div>
          <div className="text-center">
            <p className={`text-3xl font-bold ${quarantinedCount > 0 ? 'text-red-600' : 'text-slate-400'}`}>{quarantinedCount}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium uppercase tracking-wider">Quarantined</p>
          </div>
        </div>

        {/* Format breakdown */}
        <div className="mt-5 pt-4 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Format Breakdown</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(
              results.reduce((acc, r) => {
                acc[r.detected_format] = (acc[r.detected_format] || 0) + 1;
                return acc;
              }, {})
            ).map(([fmt, count]) => (
              <span key={fmt} className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-700">
                {fmt}: <strong>{count}</strong>
              </span>
            ))}
          </div>
        </div>

        {quarantinedCount > 0 && (
          <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span><strong>{quarantinedCount}</strong> event(s) failed validation and are quarantined. Click each event to view details and download a report above.</span>
          </div>
        )}

        {customPluginCount > 0 && (
          <div className="mt-2 flex items-center gap-2 bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm text-purple-700">
            <Puzzle className="w-4 h-4 flex-shrink-0" />
            <span><strong>{customPluginCount}</strong> event(s) parsed by custom plugin — no human confirmation required.</span>
          </div>
        )}
      </div>

      {/* Per-event pipeline visualization */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 text-sm font-mono text-slate-600 overflow-x-auto">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Pipeline Flow</div>
        <div className="flex flex-wrap gap-y-1">
          {results.map((r, i) => (
            <div key={i} className="mr-4 text-xs mb-1">
              <span className="text-slate-400">E{i + 1}</span>
              <span className="mx-1 text-slate-300">→</span>
              <span className="text-slate-600">{r.detected_format}</span>
              <span className="mx-1 text-slate-300">→</span>
              <span className={r.validation?.status === 'VALID' ? 'text-green-600' : 'text-red-500'}>
                {r.parser || 'N/A'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Individual events */}
      <div className="space-y-3">
        {results.map((result, i) => (
          <EventRow key={i} index={i} result={result} onPluginConfirmed={onPluginConfirmed} />
        ))}
      </div>
    </div>
  );
};

export default BatchResultView;
