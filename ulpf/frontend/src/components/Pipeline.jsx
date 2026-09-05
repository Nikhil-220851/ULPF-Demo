import React from 'react';
import { FileText, Search, Cpu, Database, CheckCircle, Package, XCircle } from 'lucide-react';

const Pipeline = ({ currentStage, result }) => {
  const isComplete = currentStage === 'universal' || currentStage === 'validate';
  const confidence = result?.confidence?.overall ? `${(result.confidence.overall * 100).toFixed(1)}%` : '...';
  const format = result?.detected_format || '...';
  const validationStatus = result?.validation?.status || '...';
  
  const stages = [
    { 
      id: 'raw', title: 'RAW LOG', icon: FileText,
      subtext: isComplete ? 'Ingested' : 'Processing...' 
    },
    { 
      id: 'detect', title: 'DETECTION', icon: Search,
      subtext: isComplete ? `${format} · ${confidence}` : '...'
    },
    { 
      id: 'parse', title: 'PARSER', icon: Cpu,
      subtext: isComplete ? `${format} Parser` : '...' 
    },
    { 
      id: 'normalize', title: 'NORMALIZATION', icon: Database,
      subtext: isComplete && result?.normalized_event ? 'Fields Mapped' : '...' 
    },
    { 
      id: 'validate', title: 'VALIDATION', icon: validationStatus === 'VALID' ? CheckCircle : XCircle,
      subtext: isComplete ? validationStatus : '...' 
    },
    { 
      id: 'universal', title: 'UNIVERSAL EVENT', icon: Package,
      subtext: currentStage === 'universal' ? 'Ready' : '...' 
    }
  ];

  const stageIndex = stages.findIndex(s => s.id === currentStage);

  return (
    <div className="w-full py-6 overflow-x-auto">
      <div className="min-w-[800px] flex justify-between items-start relative px-4">
        {/* Connecting Line */}
        <div className="absolute top-8 left-12 right-12 h-0.5 bg-slate-200 -z-10"></div>
        {stages.map((stage, idx) => {
          const isActive = stage.id === currentStage;
          const isPassed = idx < stageIndex || currentStage === 'universal';
          
          let borderColor = 'border-slate-200';
          let bgColor = 'bg-white';
          let textColor = 'text-slate-500';
          let iconColor = 'text-slate-400';
          
          if (isActive) {
             borderColor = 'border-primary-500';
             bgColor = 'bg-primary-50';
             textColor = 'text-primary-700';
             iconColor = 'text-primary-600 animate-pulse';
          } else if (isPassed) {
             if (stage.id === 'validate' && validationStatus !== 'VALID' && validationStatus !== '...') {
                borderColor = 'border-red-300';
                bgColor = 'bg-red-50';
                textColor = 'text-red-700';
                iconColor = 'text-red-500';
             } else {
                borderColor = 'border-green-300';
                bgColor = 'bg-green-50';
                textColor = 'text-green-700';
                iconColor = 'text-green-500';
             }
          }

          return (
            <div key={stage.id} className="flex flex-col items-center w-32 relative z-0 bg-background">
              <div className={`w-16 h-16 rounded-xl border-2 flex items-center justify-center mb-3 shadow-sm transition-colors ${borderColor} ${bgColor}`}>
                <stage.icon className={`w-7 h-7 ${iconColor}`} />
              </div>
              <div className={`text-xs font-bold tracking-wider mb-1 text-center ${textColor}`}>
                {stage.title}
              </div>
              <div className="text-xs text-slate-500 font-mono text-center px-2">
                {stage.subtext}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Pipeline;

