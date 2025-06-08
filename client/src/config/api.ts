export const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://resume-extractor-4523.onrender.com';

export const API_ENDPOINTS = {
  RESUMES: `${API_BASE_URL}/api/resumes`,
  UPLOAD: `${API_BASE_URL}/api/upload`,
  DELETE: (id: string) => `${API_BASE_URL}/api/resumes/${id}`
};
