import React from 'react';
import { useApp } from '../context/AppContext';
import { FileText, BookOpen } from 'lucide-react';

const SourcePane: React.FC = () => {
  const { activeCitation } = useApp();

  if (!activeCitation) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 text-center">
        <div className="w-16 h-16 bg-zinc-100 text-zinc-400 rounded-full flex items-center justify-center mb-4">
          <BookOpen className="w-8 h-8" />
        </div>
        <h3 className="text-sm font-medium text-zinc-900 mb-1">No source selected</h3>
        <p className="text-xs text-zinc-500">
          Click a citation marker in the chat to view the grounding source.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      <div className="p-4 border-b border-zinc-100 bg-zinc-50/50 shrink-0">
        <div className="flex items-center gap-2 mb-1">
          <FileText className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">Source Chunk</span>
        </div>
        <div className="flex justify-between items-end">
          <h4 className="text-sm font-semibold text-zinc-900 truncate max-w-[80%]">
            {activeCitation.source_filename}
          </h4>
          <span className="text-[10px] font-medium px-2 py-0.5 bg-zinc-200 rounded-full text-zinc-600">
            Page {activeCitation.page_number}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg shadow-sm">
          <p className="text-sm leading-relaxed text-zinc-800 italic">
            "{activeCitation.text}"
          </p>
        </div>
        <div className="mt-6 p-4 bg-zinc-50 rounded-lg border border-zinc-100">
          <h5 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-2">
            Citation Metadata
          </h5>
          <div className="grid grid-cols-2 gap-y-2 text-xs">
            <span className="text-zinc-500">Chunk Index:</span>
            <span className="text-zinc-900 font-medium">{activeCitation.chunk_index}</span>
            <span className="text-zinc-500">Source:</span>
            <span className="text-zinc-900 font-medium truncate">{activeCitation.source_filename}</span>
            <span className="text-zinc-500">Page:</span>
            <span className="text-zinc-900 font-medium">{activeCitation.page_number}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SourcePane;
