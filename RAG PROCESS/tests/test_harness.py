import time
from app.config import LOG_FILE_PATH
from app.vectorstore import get_pdf_files, build_vectorstore
from app.rag_engine import query_strict_rag_stream

# Define your test suite (questions & what key facts you expect to see)
TEST_SUITE = [
    {
        "id": 1,
        "question": "What is the main topic of this document?",
        "expected_keywords": ["overview", "summary", "introduction"]
    },
    {
        "id": 2,
        "question": "What are the key findings or conclusions?",
        "expected_keywords": ["result", "conclusion", "found"]
    },
    {
        "id": 3,
        "question": "Who is the target audience or author?",
        "expected_keywords": ["author", "prepared by", "audience"]
    }
]

def run_harness():
    pdfs = get_pdf_files()
    if not pdfs:
        print("No PDFs found in data directory. Please add a PDF first.")
        return

    print("=== RAG TEST HARNESS ===")
    print(f"Loading vectorstore for: {pdfs[0]}")
    vstore = build_vectorstore(pdfs[0])

    # Model choice: "1" for Qwen 1.5B, "2" for Llama 3.2 3B, "3" for No LLM (Raw Top-1 Chunk)
    model_choice = "1" 

    print(f"\nRunning {len(TEST_SUITE)} test cases...\n" + "="*50)

    results = []

    for test in TEST_SUITE:
        q_id = test["id"]
        query = test["question"]
        print(f"\n[Test #{q_id}] Query: '{query}'")

        start_time = time.time()
        
        # Collect streamed tokens
        full_response = ""
        for token in query_strict_rag_stream(query, model_choice, vstore):
            full_response += token
        
        elapsed_time = round(time.time() - start_time, 2)

        # Basic keyword match check
        passed_keywords = [
            kw for kw in test["expected_keywords"] 
            if kw.lower() in full_response.lower()
        ]
        
        print(f"Response ({elapsed_time}s):\n{full_response.strip()}")
        print(f"Keywords matched: {len(passed_keywords)}/{len(test['expected_keywords'])} -> {passed_keywords}")
        print("-" * 50)

        results.append({
            "id": q_id,
            "query": query,
            "time_sec": elapsed_time,
            "response_length": len(full_response),
            "matched_keywords": passed_keywords
        })

    # Summary Report
    print("\n" + "="*20 + " HARNESS SUMMARY " + "="*20)
    for r in results:
        print(f"Test #{r['id']} | Time: {r['time_sec']}s | Chars: {r['response_length']} | Keywords Found: {r['matched_keywords']}")

if __name__ == "__main__":
    run_harness()