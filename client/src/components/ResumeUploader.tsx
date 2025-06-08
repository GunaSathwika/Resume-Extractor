import React, { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FileText, X } from 'lucide-react';
import axios from 'axios';

interface ResumeUploaderProps {
  onUploadSuccess?: (id: string) => void;
}

const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = (id: string) => {
    if (onUploadSuccess) {
      onUploadSuccess(id);
    }
    navigate('/resumes', { replace: true });
  };

  const validateFile = (file: File) => {
    if (file.size > 10 * 1024 * 1024) { // 10MB
      setError('File size must be less than 10MB');
      return false;
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are allowed');
      return false;
    }
    return true;
  };

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
      setError(null);
    }
  }, []);

  const uploadFile = useCallback(async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      handleUploadSuccess(response.data.id);
      setSelectedFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  }, [selectedFile, onUploadSuccess]);

  const showError = () => {
    if (!error) return null;
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <X className="h-5 w-5 text-red-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setError(null);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setError(null);
      }
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {error && showError()}
      
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 ${
          selectedFile ? 'border-green-500 bg-green-50' : 
          dragActive ? 'border-indigo-500 bg-indigo-50' : 
          'border-gray-300'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <FileText className="h-6 w-6 text-green-500" />
              <span className="ml-3 text-sm font-medium text-green-700">{selectedFile.name}</span>
            </div>
            <div className="text-sm text-gray-500">
              {Math.round(selectedFile.size / 1024)} KB
            </div>
            <button
              onClick={handleRemoveFile}
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Remove File
            </button>
          </div>
        ) : (
          <div>
            <FileText className="h-6 w-6 text-gray-400 mb-4" />
            <div className="text-sm text-gray-600">
              Drag and drop a PDF file here, or click to select
            </div>
            <input
              id="resume-file"
              type="file"
              className="hidden"
              onChange={handleChange}
              accept=".pdf"
              aria-label="Select PDF resume file"
              title="Select PDF resume file"
            />
            <label htmlFor="resume-file" className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 cursor-pointer">
              <span>Select PDF File</span>
            </label>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="mt-4 space-y-4">
          <div className="flex justify-between items-center">
            <div>
              {!uploading && (
                <button
                  onClick={uploadFile}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Upload Resume
                </button>
              )}
              {uploading && (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
                  <p className="text-sm text-gray-600">Uploading resume...</p>
                </div>
              )}
            </div>
            <div className="flex space-x-4">
              <button
                onClick={handleRemoveFile}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Cancel
              </button>
              <Link
                to="/resumes"
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                View All Resumes
              </Link>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            {error ? (
              <span className="text-red-600">{error}</span>
            ) : (
              <span className="text-green-600">Ready to upload</span>
            )}
          </div>
        </div>
      )}

      {!selectedFile && (
        <div className="mt-4">
          <Link
            to="/resumes"
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            View All Resumes
          </Link>
        </div>
      )}

      {!selectedFile && !uploading && (
        <button
          onClick={() => document.getElementById('resume-file')?.click()}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Upload Resume
        </button>
      )}
    </div>
  );
};

export default ResumeUploader;
