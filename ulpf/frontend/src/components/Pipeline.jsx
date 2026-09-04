import React from 'react';
import { ArrowDown, FileText, Search, Cpu, Database, CheckCircle, Package } from 'lucide-react';

const PipelineStage = ({ title, icon: Icon, isActive, isCompleted }) => {
  return (
    <div className={`flex flex-col items-center p-4 border rounded-xl shadow-sm transition-all duration-300 ${isActive ? 'bg-primary-50 border-primary-500 shadow-md transform scale-105' : isCompleted ? 'bg-white border-green-200 text-slate-600' : 'bg-slate-50 border-slate-200 text-slate-400'}`}>
      <Icon className={`w-8 h-8 mb-2 ${isActive ? 'text-primary-600 animate-pulse' : isCompleted ? 'text-green-500' : 'text-slate-300'}`} />
      <span className="text-sm font-semibold text-center">{title}</span>
    </div>
  );
};

const Pipeline = ({ currentStage }) => {
  const stages = [
    { id: 'raw', title: 'Raw Log', icon: FileText },
    { id: 'detect', title: 'Format Detection', icon: Search },
    { id: 'parse', title: 'Parser', icon: Cpu },
    { id: 'normalize', title: 'Normalization', icon: Database },
    { id: 'validate', title: 'Validation', icon: CheckCircle },
    { id: 'universal', title: 'Universal Event', icon: Package }
  ];

  // For demo, if stage is universal, all are completed.
  const stageIndex = stages.findIndex(s => s.id === currentStage);
  
  return (
    <div className="w-full max-w-4xl mx-auto py-8">
      <h3 className="text-lg font-semibold text-slate-800 mb-6 text-center">Processing Pipeline</h3>
      <div className="flex justify-between items-center relative">
        {stages.map((stage, idx) => (
          <React.Fragment key={stage.id}>
            <div className="z-10 w-32">
              <PipelineStage 
                title={stage.title} 
                icon={stage.icon}
                isActive={stage.id === currentStage}
                isCompleted={idx < stageIndex || currentStage === 'universal'}
              />
            </div>
            {idx < stages.length - 1 && (
              <div className="flex-1 flex justify-center items-center -mx-2">
                <ArrowDown className={`w-6 h-6 transform -rotate-90 ${idx < stageIndex || currentStage === 'universal' ? 'text-primary-400' : 'text-slate-200'}`} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default Pipeline;
