import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAG_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://127.0.0.1:8001/api/query"
)

print("RAG URL =", RAG_URL)

def ask_rag(question: str, history: list[dict] | None = None, model_name: str = "qwen2.5:3b"):
    try:
        print("QUESTION =", question, "| MODEL =", model_name)

        payload = {
            "query": question,
            "model_name": model_name
        }
        if history:
            payload["history"] = history

        response = requests.post(
            RAG_URL,
            json=payload,
            timeout=30
        )

        print("STATUS =", response.status_code)
        print("BODY =", response.text)

        return response.json()

    except Exception as e:
        print("RAG ERROR =", str(e))
        return {
            "answer": "Sorry, I cannot find information regarding this question in the uploaded documents."
        }