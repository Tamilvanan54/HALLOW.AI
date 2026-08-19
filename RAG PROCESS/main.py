import glob
import os
import time
import warnings
from contextlib import asynccontextmanager

import fitz  # PyMuPDF
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag_engine import RAGEngine

# Suppress minor warnings for cleaner terminal output
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")
logging_level = os.environ.get("LOGLEVEL", "WARNING").upper()

load_dotenv()

# Global RAG Engine instance
engine: RAGEngine | None = None
CHROMA_PERSIST_DIR = "./chroma_db"


def extract_pdf_documents(pdf_path: str) -> list[Document]:
    """Extract text from a PDF file on a per-page basis using PyMuPDF."""
    documents = []
    file_name = os.path.basename(pdf_path)
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text and text.strip():
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": file_name, "page": page_num + 1},
                    )
                )
        doc.close()
    except Exception as e:
        print(f"⚠️ Error extracting PDF text from {pdf_path}: {e}")
    return documents


def load_all_pdfs(data_folder: str = "./data") -> list[Document]:
    """Find and chunk all PDFs from root directory and ./data folder."""
    pdf_files = []
    if os.path.exists(data_folder):
        pdf_files.extend(glob.glob(os.path.join(data_folder, "*.pdf")))

    for f in glob.glob("*.pdf"):
        if f not in pdf_files:
            pdf_files.append(f)

    if not pdf_files:
        print("❌ No PDF files found in current directory or ./data folder!")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    split_docs = []
    print("\n⏳ Auto-indexing all available documents...")
    for pdf_path in pdf_files:
        try:
            page_docs = extract_pdf_documents(pdf_path)
            file_name = os.path.basename(pdf_path)
            for page_doc in page_docs:
                chunks = text_splitter.split_documents([page_doc])
                split_docs.extend(chunks)
            print(f"   ✓ Extracted raw text: {file_name}")
        except Exception as e:
            print(f"   ❌ Error loading '{pdf_path}': {e}")

    print(f"   ✂️ Split documents into {len(split_docs)} balanced chunks.")
    return split_docs


def build_unified_vectorstore() -> Chroma | None:
    """Build or load persistent Chroma vector store with fast embeddings."""
    print("\n⏳ Initializing embeddings for vector database...")
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            encode_kwargs={"normalize_embeddings": True}
        )
        print("⚡ Using HuggingFace all-MiniLM-L6-v2 local embeddings.")
    except Exception as e:
        print(f"⚠️ Fast HuggingFaceEmbeddings unavailable ({e}). Falling back to OllamaEmbeddings...")
        embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Reuse existing vectorstore if directory exists and has data
    if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
        print("⚡ Persistent vector store found. Loading existing database...")
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )

    vectorstore = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )

    docs = load_all_pdfs()
    if not docs:
        print("ℹ️ No PDF documents found. RAG Engine initialized with empty knowledge base.")
        return vectorstore

    batch_size = 100
    total_docs = len(docs)

    print(f"⏳ Embedding {total_docs} chunks into Chroma...")
    for i in range(0, total_docs, batch_size):
        batch = docs[i : i + batch_size]
        try:
            vectorstore.add_documents(documents=batch)
            print(
                f"   ✓ Indexed chunks {i + 1} to {min(i + batch_size, total_docs)} / {total_docs}"
            )
        except Exception as err:
            print(f"   ⚠️ Warning on batch {i}: {err}. Retrying in 2 seconds...")
            time.sleep(2)
            vectorstore.add_documents(documents=batch)

    print("✅ Vector database initialized and persisted successfully!")
    return vectorstore


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global engine
    print("⏳ Loading Vectorstore & RAG Engine...")
    vectorstore = build_unified_vectorstore()

    if vectorstore:
        engine = RAGEngine(
            vectorstore=vectorstore, 
            model_name="qwen2.5:3b",
            model_kwargs={
                "keep_alive": "24h",
                "options": {
                    "num_gpu": 99,
                    "temperature": 0.0,
                    "num_predict": 90,
                    "num_ctx": 512,
                    "top_k": 10,
                    "top_p": 0.7
                }
            }
        )
        print("✅ RAG Engine Microservice is ready!")
    yield


app = FastAPI(title="RAG Microservice API", lifespan=lifespan)

# Enable CORS for external frontend or backend service integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., examples=["What is machine learning?"])
    model_name: str = Field(default="qwen2.5:3b", examples=["qwen2.5:3b"])


class IngestRequest(BaseModel):
    filename: str | None = None


class DeleteDocRequest(BaseModel):
    filename: str


def reload_vectorstore():
    """Rebuild Chroma vector store to reflect current PDFs in ./data folder."""
    global engine
    print("⏳ Rebuilding vector store from current documents in ./data...")
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            encode_kwargs={"normalize_embeddings": True}
        )
    except Exception:
        embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Clear old chroma directory if needed to remove deleted documents completely
    if os.path.exists(CHROMA_PERSIST_DIR):
        try:
            import shutil
            shutil.rmtree(CHROMA_PERSIST_DIR, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ Warning clearing chroma_db: {e}")

    docs = load_all_pdfs()
    if not docs:
        print("⚠️ No documents remaining in ./data folder.")
        new_vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
        )
    else:
        new_vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )

    if engine:
        engine.vectorstore = new_vectorstore
    else:
        engine = RAGEngine(vectorstore=new_vectorstore, model_name="qwen2.5:3b")

    print(f"✅ Vector database successfully updated with {len(docs)} document chunks.")
    return len(docs)


@app.get("/health")
def health_check():
    """Health check endpoint to verify engine readiness."""
    return {"status": "ok", "engine_ready": engine is not None}


@app.post("/api/ingest")
def handle_ingest(request: IngestRequest | None = None):
    """Ingest newly uploaded documents from ./data folder into Chroma vectorstore."""
    global engine
    if not engine:
        raise HTTPException(
            status_code=503, detail="RAG Engine is not initialized"
        )

    chunks_count = reload_vectorstore()
    return {"status": "success", "message": "Documents ingested successfully", "chunks": chunks_count}


@app.post("/api/delete-doc")
def handle_delete_doc(request: DeleteDocRequest):
    """Remove a document from ./data and rebuild vectorstore to remove its context completely."""
    global engine
    filename = request.filename
    print(f"🗑️ Deleting document from RAG: {filename}")

    rag_file_path = os.path.join("./data", filename)
    if os.path.exists(rag_file_path):
        try:
            os.remove(rag_file_path)
            print(f"✓ Removed file '{rag_file_path}'")
        except Exception as e:
            print(f"⚠️ Failed to delete '{rag_file_path}': {e}")

    chunks_count = reload_vectorstore()
    return {"status": "success", "message": f"Deleted {filename} and updated vectorstore", "remaining_chunks": chunks_count}


@app.post("/api/query")
def handle_query(request: QueryRequest):
    """Standard synchronized RAG response returning full answer and source citations."""
    if not engine:
        raise HTTPException(
            status_code=503, detail="RAG Engine is not initialized"
        )

    engine.set_model(request.model_name)

    result = engine.query(request.query)
    answer = result.get("answer", "")

    sources = [
        {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", "N/A"),
            "content": doc.page_content,
        }
        for doc in result.get("context", [])
    ]

    return {"answer": answer, "sources": sources}


@app.post("/api/query/stream")
def handle_query_stream(request: QueryRequest):
    """Streaming response returning generated answer tokens as they arrive."""
    if not engine:
        raise HTTPException(
            status_code=503, detail="RAG Engine is not initialized"
        )

    engine.set_model(request.model_name)

    def token_generator():
        for chunk in engine.query_stream(request.query):
            yield chunk

    return StreamingResponse(
        token_generator(),
        media_type="text/plain",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )