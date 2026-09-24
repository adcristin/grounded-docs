import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { Citation } from '../api/client';

interface AppState {
  currentModel: 'qwen3:4b';
  activeCitation: Citation | null;
  uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
  lastDebugMetrics: any | null;
  activeDocument: { filename: string; pointCount: number } | null;
  isFirstQuestionAsked: boolean;
  setCurrentModel: (model: 'qwen3:4b') => void;
  setActiveCitation: (citation: Citation | null) => void;
  setUploadStatus: (status: 'idle' | 'uploading' | 'success' | 'error') => void;
  setLastDebugMetrics: (metrics: any) => void;
  setActiveDocument: (doc: { filename: string; pointCount: number } | null) => void;
  setIsFirstQuestionAsked: (asked: boolean) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentModel, setCurrentModel] = useState<'qwen3:4b'>('qwen3:4b');
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [lastDebugMetrics, setLastDebugMetrics] = useState<any | null>(null);
  const [activeDocument, setActiveDocument] = useState<{ filename: string; pointCount: number } | null>(null);
  const [isFirstQuestionAsked, setIsFirstQuestionAsked] = useState(false);

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
        activeDocument,
        setActiveDocument,
        isFirstQuestionAsked,
        setIsFirstQuestionAsked,
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
