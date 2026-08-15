import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAG_URL = os.getenv("RAG_SERVICE_URL")

print("RAG URL =", RAG_URL)

def ask_rag(question):

    response = requests.post(
        RAG_URL,
        json={
            "query": question
        },
        timeout=30
    )

    return response.json()