import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Force Hugging Face transformers/sentence-transformers into strictly offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DATA_PATH = "data"
CHROMA_PATH = "chroma"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_pdf_files():
    """Returns a list of all PDF files present in the data directory."""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH, exist_ok=True)
        return []
    return [f for f in os.listdir(DATA_PATH) if f.lower().endswith(".pdf")]


def load_vectorstore():
    """Loads the unified ChromaDB persistent vectorstore created by ingest.py.

    Configured for 100% offline execution without network pinging.
    """
    if not os.path.exists(CHROMA_PATH):
        print(f"❌ Error: Vectorstore directory '{CHROMA_PATH}' not found.")
        print(
            "   Please place your PDFs inside 'data/' and run 'python ingest.py' first!"
        )
        return None

    print("\n[Loading ChromaDB]: Connecting to vector store...")

    try:
        # Pass local_files_only=True to prevent network checks
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL, model_kwargs={"local_files_only": True}
        )

        vectorstore = Chroma(
            persist_directory=CHROMA_PATH, embedding_function=embeddings
        )
        print("✅ Vector store loaded successfully!\n")
        return vectorstore
    except Exception as e:
        print(f"❌ Failed to load ChromaDB: {e}")
        return None