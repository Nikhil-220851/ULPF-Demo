import React, { useState, useRef } from 'react';
import { Upload, Play, Terminal, X, FileText, Files } from 'lucide-react';
import { parseFileIntoEvents, isMultiEvent, parsePastedText } from '../utils/fileParser';

const EXAMPLES = {
  'Syslog': 'Sep 04 10:32:15 firewall01 sshd[1234]: Accepted publickey for user admin from 192.168.1.10 port 54321 ssh2',
  'JSON': '{"timestamp": "2026-09-04T10:32:15Z", "src_ip": "192.168.1.10", "dest_ip": "10.0.0.5", "action": "ALLOW", "severity": "medium"}',
  'CEF': 'CEF:0|Security|Firewall|1.0|100|Traffic Allowed|3|src=192.168.1.10 dst=10.0.0.5 spt=443 dpt=80 act=ALLOW',
  'LEEF': 'LEEF:1.0|Security|Firewall|1.0|100|src=192.168.1.10\tdst=10.0.0.5\tact=ALLOW',
  'Key-Value': 'time="2026-09-04 10:32:15" action=ALLOW src=192.168.1.10 dst=10.0.0.5',
  'Unknown / Custom': '172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP',
  'Malformed / Invalid IP': 'src=999.999.1.10 dst=10.0.0.5 act=ALLOW',
  'Mixed (6 events)': `Sep 05 10:01:12 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 SRCPORT=443 DSTPORT=52144 PROTO=TCP ACTION=ALLOW SEVERITY=5
{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","source_port":22,"destination_port":443,"protocol":"TCP","action":"DENY"}
CEF:0|PaloAlto|Firewall|11.0|1001|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW
172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP
Sep 05 10:04:51 firewall02 SRCIP=10.1.1.15 DSTIP=192.168.10.20 SRCPORT=3389 DSTPORT=49152 PROTO=TCP ACTION=DENY SEVERITY=8
{"source_ip":"10.2.2.10","destination_ip":"172.16.1.50","source_port":53,"destination_port":53000,"protocol":"UDP","action":"ALLOW"}`
};

const SUPPORTED_EXTS = ['.txt', '.log', '.json', '.csv'];

const LogInput = ({ onProcess, onBatchProcess, isProcessing }) => {
  const [logText, setLogText] = useState('');
  // For multi-file: array of {fileName, fileSize, events}
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [fileError, setFileError] = useState('');
  const fileInputRef = useRef(null);

  const handleProcess = () => {
    if (uploadedFiles.length > 0) {
      // Build event objects with source_file provenance
      const allEvents = [];
      uploadedFiles.forEach((f, fileIdx) => {
        f.events.forEach(rawEvt => {
          allEvents.push({
            raw_payload: rawEvt,
            source_file: f.fileName,
            source_file_index: fileIdx,
          });
        });
      });

      if (allEvents.length === 1) {
        onProcess(allEvents[0].raw_payload);
      } else {
        onBatchProcess(allEvents);
      }
      return;
    }

    // Paste mode
    if (logText.trim()) {
      const eventsToProcess = parsePastedText(logText);
      if (eventsToProcess.length === 1) {
        onProcess(eventsToProcess[0]);
      } else if (eventsToProcess.length > 1) {
        onBatchProcess(eventsToProcess.map(e => ({ raw_payload: e })));
      }
    }
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    setFileError('');
    const results = [];
    const errors = [];
    let pending = files.length;

    files.forEach(file => {
      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
      if (!SUPPORTED_EXTS.includes(ext)) {
        errors.push(`Unsupported: ${file.name} (${ext})`);
        pending--;
        if (pending === 0) finish();
        return;
      }

      const reader = new FileReader();
      reader.onerror = () => {
        errors.push(`Failed to read: ${file.name}`);
        pending--;
        if (pending === 0) finish();
      };
      reader.onload = (evt) => {
        try {
          const events = parseFileIntoEvents(evt.target.result, ext);
          results.push({
            fileName: file.name,
            fileSize: (file.size / 1024).toFixed(1) + ' KB',
            events,
          });
        } catch (err) {
          errors.push(`Parse error in ${file.name}: ${err.message}`);
        }
        pending--;
        if (pending === 0) finish();
      };
      reader.readAsText(file);
    });

    const finish = () => {
      if (errors.length) setFileError(errors.join(' | '));
      setUploadedFiles(results);
      if (results.length === 1 && results[0].events.length === 1) {
        setLogText(results[0].events[0]);
      }
    };

    // Reset input so same files can be re-selected
    e.target.value = '';
  };

  const handleClear = () => {
    setUploadedFiles([]);
    setLogText('');
    setFileError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const totalEvents = uploadedFiles.reduce((s, f) => s + f.events.length, 0);
  const isMultiMode = uploadedFiles.length > 0;
  const canProcess = isMultiMode ? totalEvents > 0 : !!logText.trim();
  const pasteEvents = !isMultiMode && logText.trim() ? parsePastedText(logText) : [];
  const pasteIsMulti = pasteEvents.length > 1;
  const processLabel = isMultiMode
    ? `Process ${totalEvents} Event${totalEvents !== 1 ? 's' : ''} from ${uploadedFiles.length} File${uploadedFiles.length !== 1 ? 's' : ''}`
    : pasteIsMulti
      ? `Process ${pasteEvents.length} Events`
      : 'Process Log';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100">
        <h2 className="text-xl font-bold text-slate-800 mb-1">Process a Security Log</h2>
        <p className="text-slate-500 text-sm">Paste raw log events, select an example, or upload one or more files (.txt, .log, .json, .csv).</p>
      </div>

      <div className="p-6 bg-slate-50">
        {/* Example buttons */}
        <div className="flex space-x-2 mb-4 overflow-x-auto pb-2">
          {Object.entries(EXAMPLES).map(([name, text]) => (
            <button
              key={name}
              onClick={() => { handleClear(); setLogText(text); }}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-slate-200 text-slate-600 rounded-full hover:bg-primary-50 hover:text-primary-600 hover:border-primary-200 transition-colors whitespace-nowrap"
            >
              {name}
            </button>
          ))}
        </div>

        {/* Textarea — hidden when files are uploaded */}
        {!isMultiMode && (
          <div className="relative">
            <div className="absolute top-3 left-3 text-slate-400">
              <Terminal className="w-5 h-5" />
            </div>
            <textarea
              value={logText}
              onChange={(e) => setLogText(e.target.value)}
              placeholder="Paste a raw log event here, or upload file(s) below..."
              className="w-full h-48 pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm resize-none"
              spellCheck="false"
            />
            {pasteIsMulti && (
              <div className="mt-1 text-xs text-blue-600 font-medium pl-1">
                {pasteEvents.length} events detected in pasted text — will be processed as a batch.
              </div>
            )}
          </div>
        )}

        {/* Multi-file summary */}
        {isMultiMode && (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 bg-blue-50 border-b border-blue-100">
              <div className="flex items-center gap-2 text-blue-800 font-semibold text-sm">
                <Files className="w-4 h-4" />
                Selected Files — {totalEvents} total events
              </div>
              <button onClick={handleClear} className="text-blue-400 hover:text-red-500 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="divide-y divide-slate-100">
              {uploadedFiles.map((f, idx) => (
                <div key={idx} className="flex items-center gap-3 px-4 py-3 text-sm">
                  <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  <span className="font-medium text-slate-800 flex-1 truncate">{f.fileName}</span>
                  <span className="text-slate-400 text-xs">{f.fileSize}</span>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 font-bold rounded-full text-xs">
                    {f.events.length} event{f.events.length !== 1 ? 's' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {fileError && (
          <div className="mt-3 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5 text-sm text-red-700">
            <span>{fileError}</span>
            <button onClick={() => setFileError('')} className="ml-auto"><X className="w-4 h-4" /></button>
          </div>
        )}

        {/* Bottom row */}
        <div className="mt-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".txt,.log,.json,.csv"
              multiple
            />
            <button
              onClick={() => fileInputRef.current.click()}
              className="flex items-center space-x-2 text-sm text-slate-500 hover:text-slate-800 font-medium transition-colors"
            >
              <Upload className="w-4 h-4" />
              <span>Upload File{isMultiMode ? 's' : ''}</span>
            </button>
          </div>

          <button
            onClick={handleProcess}
            disabled={!canProcess || isProcessing}
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
                <span>{processLabel}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogInput;
