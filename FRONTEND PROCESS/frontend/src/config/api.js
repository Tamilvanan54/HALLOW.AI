const getHost = () => {
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    return window.location.hostname;
  }
  return '127.0.0.1';
};

const host = getHost();
const isLocal = host === 'localhost' || host === '127.0.0.1';

// Direct port mapping for robust API communication
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (isLocal ? 'http://127.0.0.1:8000' : `http://${host}:8000`);

export const RAG_BASE_URL = import.meta.env.VITE_RAG_URL ||
  (isLocal ? 'http://127.0.0.1:8001' : `http://${host}:8001`);
