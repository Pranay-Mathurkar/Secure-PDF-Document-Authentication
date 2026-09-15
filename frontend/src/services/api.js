import axios from 'axios';

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for PDF rendering
});

/**
 * Check health status of the FastAPI backend
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Backend health check failed:', error);
    throw error;
  }
};

/**
 * Upload original PDF and generate a 2-page secured document
 * @param {File} file - Original PDF file
 * @param {Function} onProgress - Progress callback (0-100)
 */
export const generateSecurePdf = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/generate/secure-pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

/**
 * Upload secured 2-page PDF and verify authenticity
 * @param {File} file - Secured PDF file
 * @param {Function} onProgress - Progress callback (0-100)
 */
export const verifyPdf = async (file, originalFile, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  if (originalFile) {
    formData.append('original_file', originalFile);
  }

  const response = await apiClient.post('/verify/verify-pdf', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

/**
 * Construct absolute download URL for secured PDF
 * @param {string} relativeOrAbsoluteUrl
 */
export const getFullDownloadUrl = (downloadUrl) => {
  if (!downloadUrl) return '#';
  if (downloadUrl.startsWith('http://') || downloadUrl.startsWith('https://')) {
    return downloadUrl;
  }
  // If starts with /api/v1
  const baseUrlHost = API_BASE_URL.replace('/api/v1', '');
  return `${baseUrlHost}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
};

export default apiClient;
