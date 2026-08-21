import glob
import os
import time
import json
import warnings
from contextlib import asynccontextmanager

import fitz  # PyMuPDF
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag_engine import RAGEngine, EXACT_REFUSAL_MESSAGE
from app.spelling import extract_pdf_vocabulary

# Suppress minor warnings for cleaner terminal output
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

load_dotenv()

# Global RAG Engine instance
engine: RAGEngine | None = None
CHROMA_PERSIST_DIR = "./chroma_db"

def extract_pdf_documents(pdf_path: str) -> list[Document]:
    """Extract text from a PDF file on a per-page basis using PyMuPDF and Tesseract/EasyOCR for scanned image pages."""
    import io
    from PIL import Image

    documents = []
    file_name = os.path.basename(pdf_path)
    try:
        doc = fitz.open(pdf_path)
        ocr_type = None
        ocr_engine = None

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            # If page lacks digital text (scanned image page), run fast Tesseract OCR
            if not text or len(text) < 15:
                try:
                    images = page.get_images(full=True)
                    if images:
                        pix = page.get_pixmap(dpi=120)
                        img_bytes = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_bytes))

                        if ocr_engine is None:
                            try:
                                import pytesseract
                                pytesseract.image_to_string(img)
                                ocr_engine = pytesseract
                            except Exception:
                                ocr_engine = False

                        if ocr_engine:
                            ocr_text = ocr_engine.image_to_string(img).strip()
                            if ocr_text:
                                text = ocr_text
                except Exception as ocr_err:
                    print(f"   ⚠️ Page {page_num + 1} OCR note: {ocr_err}")

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

def load_all_pdfs() -> tuple[list[Document], set[str]]:
    """Find and chunk all PDFs inside ./data and uploads folders."""
    search_dirs = ["./data", "../uploads", "./uploads", "../BACKEND PROCESS/uploads"]
    pdf_files = []

    for d in search_dirs:
        if os.path.exists(d):
            found = glob.glob(os.path.join(d, "*.pdf"))
            for f in found:
                abs_f = os.path.abspath(f)
                if abs_f not in [os.path.abspath(p) for p in pdf_files]:
                    pdf_files.append(f)

    if not pdf_files:
        print("❌ No PDF files found in search directories!")
        return [], set()

    print(f"📄 Found {len(pdf_files)} PDF documents: {[os.path.basename(f) for f in pdf_files]}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    split_docs = []
    raw_page_docs = []
    print("\n⏳ Auto-indexing all available documents...")
    for pdf_path in pdf_files:
        try:
            page_docs = extract_pdf_documents(pdf_path)
            raw_page_docs.extend(page_docs)
            file_name = os.path.basename(pdf_path)
            for page_doc in page_docs:
                chunks = text_splitter.split_documents([page_doc])
                split_docs.extend(chunks)
            print(f"   ✓ Extracted raw text: {file_name}")
        except Exception as e:
            print(f"   ❌ Error loading '{pdf_path}': {e}")

    pdf_vocab = extract_pdf_vocabulary(raw_page_docs)
    print(f"   ✂️ Split documents into {len(split_docs)} balanced chunks. Vocabulary size: {len(pdf_vocab)} terms.")
    return split_docs, pdf_vocab

def build_unified_vectorstore() -> tuple[Chroma | None, set[str]]:
    """Build or refresh persistent Chroma vector store with fast embeddings."""
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

    # Fast startup: If persistent database already exists and contains documents, load it immediately
    if os.path.exists(CHROMA_PERSIST_DIR) and os.path.isdir(CHROMA_PERSIST_DIR) and len(os.listdir(CHROMA_PERSIST_DIR)) > 0:
        print("⚡ Loading existing persistent Chroma vector database...")
        try:
            vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=embeddings,
            )
            doc_count = vectorstore._collection.count()
            print(f"📊 Vectorstore contains {doc_count} document chunks.")
            if doc_count > 0:
                print("✅ Vector database loaded successfully!")
                return vectorstore, set()
            print("⚠️ Persistent Chroma database is empty (0 chunks). Triggering full fresh indexing...")
        except Exception as err:
            print(f"⚠️ Warning checking vector database: {err}. Rebuilding...")

    docs, pdf_vocab = load_all_pdfs()

    vectorstore = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings,
    )

    if not docs:
        print("ℹ️ No PDF documents found. RAG Engine initialized with empty knowledge base.")
        return vectorstore, set()

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
    return vectorstore, pdf_vocab

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global engine
    print("⏳ Starting RAG Engine Microservice...")

    def _async_init():
        global engine
        try:
            print("⏳ Loading Vectorstore & RAG Engine in background thread...")
            vectorstore, pdf_vocab = build_unified_vectorstore()
            model_name = os.getenv("RAG_MODEL_NAME", "qwen2.5:1.5b")
            if vectorstore:
                engine = RAGEngine(
                    vectorstore=vectorstore,
                    model_name=model_name,
                    model_kwargs={
                        "keep_alive": "24h",
                        "options": {
                            "num_gpu": 0,
                            "temperature": 0.0,
                            "num_predict": 140,
                            "num_ctx": 200,
                            "num_thread": 4,
                            "top_k": 5,
                            "top_p": 0.5
                        }
                    }
                )
                engine.pdf_vocabulary = pdf_vocab
                print("✅ RAG Engine Microservice is fully ready and online!")
        except Exception as err:
            print(f"❌ Async RAG initialization error: {err}")

    import threading
    threading.Thread(target=_async_init, daemon=True).start()

    yield
    print("👋 Shutting down RAG Engine Microservice...")

app = FastAPI(title="RAG Microservice API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Any

class QueryRequest(BaseModel):
    query: str = Field(..., examples=["What is Machine Learning?"])
    model_name: str | None = Field(default="qwen2.5:1.5b")
    history: Any | None = None

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

    docs, pdf_vocab = load_all_pdfs()

    if os.path.exists(CHROMA_PERSIST_DIR):
        try:
            import shutil
            shutil.rmtree(CHROMA_PERSIST_DIR, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ Warning clearing chroma_db: {e}")
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
        engine.pdf_vocabulary = pdf_vocab
    else:
        engine = RAGEngine(vectorstore=new_vectorstore, model_name=os.getenv("RAG_MODEL_NAME", "qwen2.5:1.5b"))
        engine.pdf_vocabulary = pdf_vocab

    print(f"✅ Vector database successfully updated with {len(docs)} document chunks.")
    return len(docs)

@app.get("/health")
def health_check():
    """Health check endpoint to verify engine readiness."""
    return {"status": "ok", "engine_ready": engine is not None}

@app.post("/api/ingest")
def handle_ingest(request: IngestRequest | None = None):
    """Ingest newly uploaded documents from ./data folder into Chroma vectorstore asynchronously."""
    global engine
    import threading
    def _async_ingest():
        try:
            print("⏳ Background document indexing started...")
            chunks = reload_vectorstore()
            print(f"✅ Background indexing complete with {chunks} chunks!")
        except Exception as err:
            print(f"❌ Background indexing error: {err}")

    threading.Thread(target=_async_ingest, daemon=True).start()
    return {"status": "success", "message": "Document indexing started in background"}

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
    """Standard synchronized RAG response returning full structured response metadata."""
    if not engine:
        raise HTTPException(status_code=503, detail="RAG Engine is not initialized")

    if request.model_name:
        engine.set_model(request.model_name)

    # Collect SSE output generator into structured JSON
    events = list(engine.query_stream_sse(request.query, history=request.history))
    
    # Parse final event data
    final_data = {}
    for event_str in reversed(events):
        if "event: final" in event_str:
            data_line = [l for l in event_str.split("\n") if l.startswith("data: ")][0]
            final_data = json.loads(data_line.replace("data: ", ""))
            break

    if not final_data:
        final_data = {
            "answer": EXACT_REFUSAL_MESSAGE,
            "sources": [],
            "confidence": "refused",
            "refusal_reason": "unknown_error",
            "corrected_query": None
        }

    return JSONResponse(content=final_data)

@app.post("/api/query/stream")
@app.post("/api/query/sse")
def handle_query_stream(request: QueryRequest):
    """SSE streaming endpoint returning status, meta, tokens, and final response metadata."""
    if not engine:
        print("⏳ Lazily initializing RAG engine on query request...")
        reload_vectorstore()

    if request.model_name and engine:
        engine.set_model(request.model_name)

    return StreamingResponse(
        engine.query_stream_sse(request.query, history=request.history),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)