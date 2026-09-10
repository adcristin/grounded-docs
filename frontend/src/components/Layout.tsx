import React from 'react';
import ChatPane from './ChatPane';
import SourcePane from './SourcePane';
import DebugPane from './DebugPane';
import { useApp } from '../context/AppContext';

const Layout: React.FC = () => {
  const { currentModel, setCurrentModel } = useApp();

  return (
    <div className="flex flex-col h-screen w-screen bg-zinc-50 text-zinc-900 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-zinc-200 shrink-0">
        <h1 className="text-xl font-bold tracking-tight">Grounded Docs</h1>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-zinc-500">Model:</span>
          <div className="flex p-1 bg-zinc-100 rounded-lg border border-zinc-200">
            {(['qwen3:4b', 'qwen3:8b'] as const).map((model) => (
              <button
                key={model}
                onClick={() => setCurrentModel(model)}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                  currentModel === model
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-zinc-500 hover:text-zinc-700'
                }`}
              >
                {model}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Chat Pane - Primary */}
        <main className="flex-1 overflow-hidden relative">
          <ChatPane />
        </main>

        {/* Source Pane - Right */}
        <aside className="w-1/3 border-l border-zinc-200 bg-white overflow-hidden hidden lg:block">
          <SourcePane />
        </aside>
      </div>

      {/* Debug Pane - Bottom Overlay */}
      <DebugPane />
    </div>
  );
};

export default Layout;
