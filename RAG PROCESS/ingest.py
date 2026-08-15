import gc
import io
import os
import re
import shutil
import time
import warnings

# Suppress noisy PyTorch deprecation and dataloader warnings
warnings.filterwarnings("ignore")

import chromadb
import easyocr
import fitz  # PyMuPDF
import torch
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Force Hugging Face transformers into offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DATA_PATH = "data"
CHROMA_PATH = "chroma"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TEMP_IMAGE_PATH = "temp_extracted_image.png"

# Toggle Vision Parsing (Set False for pure text speed, True if you need chart descriptions)
ENABLE_VISION = True

# Detect CUDA availability
has_gpu = torch.cuda.is_available()
device_type = "cuda" if has_gpu else "cpu"
print(f"[Initialization]: Loading EasyOCR engine (GPU Enabled: {has_gpu})...")
ocr_reader = easyocr.Reader(["en"], gpu=has_gpu)

if ENABLE_VISION:
    print("[Initialization]: Loading Qwen Vision Model...")
    vision_llm = OllamaLLM(model="qwen3-vl:2b")


def extract_text_and_images_from_pdf(pdf_path: str):
    """Fast PDF extraction: Reads digital text layers immediately and only invokes VLM/OCR
    for large diagrams or fully scanned pages.
    """
    doc = fitz.open(pdf_path)
    processed_documents = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_content = page.get_text().strip()

        # SPEED OPTIMIZATION 1: If page already has rich digital text (>100 chars),
        # skip VLM vision model calls on minor embedded inline images/formulas.
        if len(text_content) > 100 or not ENABLE_VISION:
            if text_content:
                metadata = {
                    "source": os.path.basename(pdf_path),
                    "page": page_num + 1,
                }
                processed_documents.append(
                    Document(page_content=text_content, metadata=metadata)
                )
            continue

        # SPEED OPTIMIZATION 2: Only analyze images if page lacks digital text (scanned page/chart)
        image_descriptions = []
        image_list = page.get_images(full=True)

        # Process at most 2 significant images per scanned page to prevent freezes
        for img_index, img_info in enumerate(image_list[:2]):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            try:
                # Ignore small icons, logos, bullets (<300x300 px)
                image = Image.open(io.BytesIO(image_bytes))
                if image.width < 300 or image.height < 300:
                    continue

                image.save(TEMP_IMAGE_PATH)

                # Quick EasyOCR
                try:
                    ocr_results = ocr_reader.readtext(
                        TEMP_IMAGE_PATH, detail=0
                    )
                    extracted_ocr_text = " ".join(ocr_results).strip()
                except Exception:
                    extracted_ocr_text = ""

                # Fast Vision Analysis
                try:
                    prompt = "Summarize key data, labels, or text in this chart/diagram briefly."
                    vision_summary = vision_llm.invoke(
                        prompt, images=[TEMP_IMAGE_PATH]
                    ).strip()
                except Exception:
                    vision_summary = "Image details skipped."

                combined_image_analysis = (
                    f"[DIAGRAM ANALYSIS - Page {page_num + 1}]\n"
                    f"OCR Text: {extracted_ocr_text}\n"
                    f"Visual Context: {vision_summary}\n"
                )
                image_descriptions.append(combined_image_analysis)

            except Exception:
                pass
            finally:
                if os.path.exists(TEMP_IMAGE_PATH):
                    try:
                        os.remove(TEMP_IMAGE_PATH)
                    except OSError:
                        pass

        full_page_content = text_content
        if image_descriptions:
            full_page_content += "\n\n" + "\n\n".join(image_descriptions)

        if full_page_content.strip():
            metadata = {
                "source": os.path.basename(pdf_path),
                "page": page_num + 1,
            }
            processed_documents.append(
                Document(page_content=full_page_content, metadata=metadata)
            )

    doc.close()
    return processed_documents


def reset_chroma_collection():
    """Resets the ChromaDB collection using native API without OS lock issues."""
    if os.path.exists(CHROMA_PATH):
        try:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            collections = client.list_collections()
            for col in collections:
                client.delete_collection(name=col.name)
            print("🧹 [CLEANUP]: Chroma DB cleared using Native API.")
        except Exception as e:
            print(f"⚠️ Warning during ChromaDB reset: {e}")


def process_all_pdfs():
    """Reads all PDFs in DATA_PATH, processes text/images, and saves to ChromaDB."""
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"Created '{DATA_PATH}' directory.")
        return

    reset_chroma_collection()

    pdf_files = [
        f for f in os.listdir(DATA_PATH) if f.lower().endswith(".pdf")
    ]
    if not pdf_files:
        print(f"❌ No PDF files found in '{DATA_PATH}/'.")
        return

    print(f"\n🚀 Found {len(pdf_files)} PDF file(s) for processing.")
    all_extracted_docs = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(DATA_PATH, pdf_file)
        print(f"[Processing PDF]: Parsing '{pdf_file}'...")
        start_time = time.time()
        docs = extract_text_and_images_from_pdf(pdf_path)
        all_extracted_docs.extend(docs)
        print(f"  └─ Finished '{pdf_file}' in {round(time.time() - start_time, 2)} seconds.")

    if not all_extracted_docs:
        print("❌ No text could be extracted.")
        return

    print("\n[Text Chunking]: Splitting content...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunked_docs = text_splitter.split_documents(all_extracted_docs)
    print(f" Created {len(chunked_docs)} chunks.")

    # HIGH-SPEED GPU ACCELERATED BATCH EMBEDDINGS
    print(f"\n[Creating Embeddings]: Loading HuggingFace model on GPU/Device ({device_type})...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={
            "device": device_type,
            "local_files_only": True
        },
        encode_kwargs={
            "batch_size": 64,  # Process 64 chunks simultaneously on GPU
            "normalize_embeddings": True
        }
    )

    print(f"\n[ChromaDB Ingestion]: Writing vector embeddings to '{CHROMA_PATH}'...")
    db_start_time = time.time()
    Chroma.from_documents(
        documents=chunked_docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )
    print(f"  └─ Vector DB write completed in {round(time.time() - db_start_time, 2)} seconds.")

    print("\n✅ Success! Vector Database successfully updated & synchronized.\n")


class PDFAutoScanner(FileSystemEventHandler):
    def __init__(self):
        self.last_triggered = 0

    def on_any_event(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".pdf"):
            return

        current_time = time.time()
        if current_time - self.last_triggered > 3:
            self.last_triggered = current_time
            print(f"\n📌 [AUTO SCAN]: Change in '{os.path.basename(event.src_path)}'")
            process_all_pdfs()


def start_auto_monitoring():
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    event_handler = PDFAutoScanner()
    observer = Observer()
    observer.schedule(event_handler, path=DATA_PATH, recursive=False)
    observer.start()

    print(f"\n👀 [LLM CORE]: Watching '{DATA_PATH}/' for PDF updates...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Automatic monitoring stopped.")
    observer.join()


if __name__ == "__main__":
    process_all_pdfs()
    start_auto_monitoring()