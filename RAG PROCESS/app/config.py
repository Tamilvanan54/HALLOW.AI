import os

# Base Directories and Paths
PDF_DIRECTORY = "./data"
LOG_FILE_PATH = "rag_history_log.txt"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Model Selections Mapping
MODEL_MAPPING = {
    "1": ("Qwen 2.5 1.5B", "qwen2.5:1.5b"),
    "2": ("Llama 3.2 3B", "llama3.2:3b"),
}

# Keywords to detect if query demands detailed analysis vs quick answer
DETAIL_KEYWORDS = [
    "explain",
    "detail",
    "briefly",
    "step by step",
    "deep dive",
    "elaborate",
    "how does",
    "why",
]

# Ensure data directory exists on import
if not os.path.exists(PDF_DIRECTORY):
    os.makedirs(PDF_DIRECTORY, exist_ok=True)