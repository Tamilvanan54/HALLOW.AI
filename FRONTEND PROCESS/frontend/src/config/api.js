const defaultHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const protocol = typeof window !== 'undefined' ? window.location.protocol : 'http:';

export const API_BASE_URL = import.meta.env.VITE_API_URL || `${protocol}//${defaultHost}:8000`;
export const RAG_BASE_URL = import.meta.env.VITE_RAG_URL || `${protocol}//${defaultHost}:8001`;
