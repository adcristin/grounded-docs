import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Citation } from '../api/client';

interface AppState {
  currentModel: 'qwen3:4b' | 'qwen3:8b';
  activeCitation: Citation | null;
  uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
  lastDebugMetrics: any | null;
  setCurrentModel: (model: 'qwen3:4b' | 'qwen3:8b') => void;
  setActiveCitation: (citation: Citation | null) => void;
  setUploadStatus: (status: 'idle' | 'uploading' | 'success' | 'error') => void;
  setLastDebugMetrics: (metrics: any) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentModel, setCurrentModel] = useState<'qwen3:4b' | 'qwen3:8b'>('qwen3:4b');
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [lastDebugMetrics, setLastDebugMetrics] = useState<any | null>(null);

  return (
    <AppContext.Provider
      value={{
        currentModel,
        setCurrentModel,
        activeCitation,
        setActiveCitation,
        uploadStatus,
        setUploadStatus,
        lastDebugMetrics,
        setLastDebugMetrics,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
