import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, Loader2, AlertCircle } from 'lucide-react';
import { api, ChatResponse, Citation } from '../api/client';
import { useApp } from '../context/AppContext';
import { cn } from '../lib/utils';
import FileUploadZone from './FileUploadZone';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  debug?: any;
}

const CitationMarker: React.FC<{
  index: number;
  citations: Citation[];
  onSelect: (c: Citation) => void
}> = ({ index, citations, onSelect }) => {
  const citation = citations.find(c => c.chunk_index === index);

  if (!citation) {
    return <span className="text-zinc-400 opacity-50">[{index}]</span>;
  }

  return (
    <button
      onClick={() => onSelect(citation)}
      className="inline-flex items-center justify-center w-4 h-4 mx-0.5 text-[10px] font-bold text-white bg-blue-500 rounded-full hover:bg-blue-600 transition-colors"
    >
      {index}
    </button>
  );
};

const ChatPane: React.FC = () => {
  const { currentModel, setActiveCitation, setUploadStatus, setLastDebugMetrics } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isPending, setIsPending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isPending) return;

    const userQuery = inputValue.trim();
    setInputValue('');

    const userMsg: Message = { role: 'user', content: userQuery };
    setMessages(prev => [...prev, userMsg]);
    setIsPending(true);

    try {
      const response = await api.chat({ query: userQuery, model: currentModel });
      setLastDebugMetrics(response.debug);

      const assistantMsg: Message = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        debug: response.debug,
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'An error occurred while processing your request. Please try again.',
        citations: []
      }]);
    } finally {
      setIsPending(false);
    }
  };

  const renderContent = (msg: Message) => {
    if (msg.role === 'assistant') {
      // Check for "Insufficient context" state
      const isInsufficient = msg.content.includes('Insufficient context to answer the question');

      if (isInsufficient) {
        return (
          <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <p className="text-sm font-medium">{msg.content}</p>
          </div>
        );
      }

      // Normal answer with citation markers
      const parts = msg.content.split(/(\[\d+\])/g);
      return (
        <div className="text-sm leading-relaxed text-zinc-700">
          {parts.map((part, i) => {
            const match = part.match(/^\[(\d+)\]$/);
            if (match) {
              const index = parseInt(match[1], 10);
              return (
                <CitationMarker
                  key={i}
                  index={index}
                  citations={msg.citations || []}
                  onSelect={setActiveCitation}
                />
              );
            }
            return <span key={i}>{part}</span>;
          })}
        </div>
      );
    }
    return <p className="text-sm text-zinc-600">{msg.content}</p>;
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages List */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <FileUploadZone onUploadSuccess={() => {}} />
            <div className="mt-8">
              <h2 className="text-lg font-semibold mb-2">How can I help you?</h2>
              <p className="text-sm text-zinc-500 max-w-sm">
                Ask questions about your uploaded documents. Answers are strictly grounded in the retrieved context.
              </p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex w-full gap-3",
              msg.role === 'user' ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center shrink-0 border border-zinc-200">
                <span className="text-[10px] font-bold text-zinc-500">AI</span>
              </div>
            )}
            <div className={cn(
              "max-w-[80%] p-3 rounded-2xl",
              msg.role === 'user'
                ? "bg-blue-600 text-white rounded-tr-none"
                : "bg-zinc-100 text-zinc-800 rounded-tl-none border border-zinc-200"
            )}>
              {renderContent(msg)}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 border border-blue-200">
                <span className="text-[10px] font-bold text-blue-600">ME</span>
              </div>
            )}
          </div>
        ))}
        {isPending && (
          <div className="flex justify-start gap-3">
            <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center shrink-0 border border-zinc-200">
              <span className="text-[10px] font-bold text-zinc-500">AI</span>
            </div>
            <div className="bg-zinc-100 p-3 rounded-2xl rounded-tl-none border border-zinc-200">
              <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 border-t border-zinc-100 bg-white">
        <div className="relative max-w-4xl mx-auto">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a question..."
            className="w-full pl-4 pr-12 py-3 bg-zinc-50 border border-zinc-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none h-14"
            rows={1}
            disabled={isPending}
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isPending}
            className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-all"
          >
            {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-[10px] text-center text-zinc-400 mt-3">
          Grounded answers only. All claims are cited from source chunks.
        </p>
      </div>
    </div>
  );
};

export default ChatPane;
