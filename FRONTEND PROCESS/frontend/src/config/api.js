const isLocalhost = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// On localhost: hit backend/rag ports directly
// On hosted server: use Nginx reverse proxy paths (/api, /rag)
export const API_BASE_URL = import.meta.env.VITE_API_URL ||
  (isLocalhost ? 'http://127.0.0.1:8000' : '/api');

export const RAG_BASE_URL = import.meta.env.VITE_RAG_URL ||
  (isLocalhost ? 'http://127.0.0.1:8001' : '/rag');
