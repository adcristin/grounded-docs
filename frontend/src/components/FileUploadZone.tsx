import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';
import { cn } from '../lib/utils';

const FileUploadZone: React.FC<{ onUploadSuccess?: () => void }> = ({ onUploadSuccess }) => {
  const { uploadStatus, setUploadStatus } = useApp();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setErrorMessage(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] },
    multiple: false,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setErrorMessage(null);

    try {
      await api.uploadDocument(selectedFile);
      setUploadStatus('success');
      if (onUploadSuccess) onUploadSuccess();

      // Reset after 3 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setSelectedFile(null);
      }, 3000);
    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setErrorMessage(error.response?.data?.detail || 'Failed to upload document. Please try again.');
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setErrorMessage(null);
  };

  return (
    <div className="w-full max-w-lg mx-auto p-6">
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer",
          isDragActive
            ? "border-blue-500 bg-blue-50 ring-4 ring-blue-500/10"
            : "border-zinc-300 bg-zinc-50 hover:border-zinc-400 hover:bg-zinc-100",
          selectedFile && "pointer-events-none"
        )}
      >
        <input {...getInputProps()} />

        {!selectedFile ? (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center mb-4 border border-zinc-200">
              <Upload className="w-6 h-6 text-zinc-500" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-900 mb-1">Upload document</h3>
            <p className="text-xs text-zinc-500">Drag & drop PDF or TXT files here</p>
            <p className="text-[10px] text-zinc-400 mt-4">Max file size: 10MB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
              <File className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-900 mb-1 truncate max-w-xs">
              {selectedFile.name}
            </h3>
            <p className="text-xs text-zinc-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <button
            onClick={removeFile}
            className="px-4 py-2 text-xs font-medium text-zinc-600 hover:text-zinc-800 transition-colors"
          >
            Remove
          </button>
          <button
            onClick={handleUpload}
            disabled={uploadStatus === 'uploading'}
            className="px-6 py-2 bg-blue-600 text-white text-xs font-bold rounded-xl hover:bg-blue-700 disabled:bg-zinc-300 transition-all flex items-center gap-2"
          >
            {uploadStatus === 'uploading' ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                Uploading...
              </>
            ) : (
              'Upload to Index'
            )}
          </button>
        </div>
      )}

      {uploadStatus === 'success' && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 text-green-800 rounded-xl flex items-center gap-3 text-xs font-medium">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          Document processed successfully!
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-800 rounded-xl flex items-center gap-3 text-xs font-medium">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {errorMessage}
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;
