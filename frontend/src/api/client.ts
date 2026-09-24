import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface UploadResponse {
  status: string;
  message: string;
  data: any;
}

export interface ChatRequest {
  query: string;
  model?: string;
}

export interface Citation {
  chunk_index: number;
  source_filename: string;
  page_number: string | number;
  text: string;
}

export interface ChatDebug {
  grounded: boolean;
  initial_top_score: number;
  rerank_top_score: number;
  chunk_count: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  debug: ChatDebug;
}

export interface StatusResponse {
  active_document: string | null;
  point_count: number;
}

export const api = {
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post('/api/chat', request);
    return response.data;
  },

  async getStatus(): Promise<StatusResponse> {
    const response = await apiClient.get('/api/status');
    return response.data;
  },

  async clearCollection(): Promise<{ status: string; message: string }> {
    const response = await apiClient.post('/api/clear');
    return response.data;
  },
};
