import React, { useState } from 'react';
import Header from './components/Header';
import LogInput from './components/LogInput';
import Pipeline from './components/Pipeline';
import ResultView from './components/ResultView';
import { processLog } from './api/client';

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelineStage, setPipelineStage] = useState(null); // 'raw', 'detect', 'parse', 'normalize', 'validate', 'universal'
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleProcess = async (rawPayload) => {
    setIsProcessing(true);
    setResult(null);
    setError(null);
    
    // Simulate pipeline stages visually before API call completes for demo purposes
    const stages = ['raw', 'detect', 'parse', 'normalize', 'validate', 'universal'];
    
    let currentIdx = 0;
    setPipelineStage(stages[currentIdx]);
    
    const interval = setInterval(() => {
      currentIdx++;
      if (currentIdx < stages.length) {
        setPipelineStage(stages[currentIdx]);
      }
    }, 400);

    try {
      const data = await processLog(rawPayload);
      clearInterval(interval);
      setPipelineStage('universal');
      setResult(data);
    } catch (err) {
      clearInterval(interval);
      setPipelineStage('validate'); // stop at validate on error usually
      setError("Unable to connect to the ULPF processing service.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="text-3xl font-bold text-slate-800 tracking-tight mb-3">
            Universal Log Pre-Processing Framework
          </h2>
          <p className="text-slate-500">
            Transform heterogeneous security logs into standardized, lossless and analytics-ready events.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-12">
            <LogInput onProcess={handleProcess} isProcessing={isProcessing} />
          </div>
          
          {(pipelineStage || result || error) && (
            <div className="lg:col-span-12">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <Pipeline currentStage={pipelineStage} />
                
                <div className="mt-8 border-t border-slate-100 pt-8">
                  {error ? (
                    <div className="bg-red-50 p-6 rounded-xl border border-red-200 text-center">
                      <h3 className="text-lg font-semibold text-red-800 mb-2">Processing Error</h3>
                      <p className="text-sm text-red-600">{error}</p>
                      <button 
                        onClick={() => handleProcess("")} // This won't work perfectly for retry, just a mock
                        className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200"
                      >
                        Retry
                      </button>
                    </div>
                  ) : result ? (
                    <ResultView result={result} />
                  ) : (
                    <div className="text-center text-slate-400 py-12 animate-pulse">
                      Analyzing and processing log event...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
