import React, { useState } from 'react';
import { ChevronUp, ChevronDown, Activity, ShieldCheck, ShieldAlert, Database } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../lib/utils';

interface DebugMetrics {
  grounded: boolean;
  initial_top_score: number;
  rerank_top_score: number;
  chunk_count: number;
}

const DebugPane: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { lastDebugMetrics } = useApp();

  return (
    <div className={cn(
      "fixed bottom-0 left-0 right-0 z-50 transition-all duration-300 ease-in-out",
      isOpen ? "h-64" : "h-10"
    )}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full h-10 bg-zinc-900 text-zinc-400 hover:text-white flex items-center justify-center gap-2 transition-colors"
      >
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        <span className="text-[10px] font-bold uppercase tracking-widest">Debug Panel</span>
      </button>

      {isOpen && (
        <div className="h-[calc(100%-40px)] bg-zinc-900 border-t border-zinc-800 p-6 text-zinc-300 overflow-y-auto">
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">

            <div className="p-4 bg-zinc-800/50 rounded-xl border border-zinc-700">
              <div className="flex items-center gap-2 mb-3 text-zinc-400">
                <ShieldCheck className="w-4 h-4" />
                <span className="text-xs font-bold uppercase">Groundedness</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-white">
                  {lastDebugMetrics?.grounded ? 'PASSED' : 'FAILED'}
                </span>
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  lastDebugMetrics?.grounded ? "bg-green-500" : "bg-red-500"
                )} />
              </div>
            </div>

            <div className="p-4 bg-zinc-800/50 rounded-xl border border-zinc-700">
              <div className="flex items-center gap-2 mb-3 text-zinc-400">
                <Activity className="w-4 h-4" />
                <span className="text-xs font-bold uppercase">Similarity Scores</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">Initial Top:</span>
                  <span className="font-mono text-zinc-200">{lastDebugMetrics?.initial_top_score.toFixed(4) || '0.0000'}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">Rerank Top:</span>
                  <span className="font-mono text-zinc-200">{lastDebugMetrics?.rerank_top_score.toFixed(4) || '0.0000'}</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-zinc-800/50 rounded-xl border border-zinc-700">
              <div className="flex items-center gap-2 mb-3 text-zinc-400">
                <Database className="w-4 h-4" />
                <span className="text-xs font-bold uppercase">Retrieval</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-white">
                  {lastDebugMetrics?.chunk_count || 0}
                </span>
                <span className="text-xs text-zinc-500">chunks retrieved</span>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};

export default DebugPane;
