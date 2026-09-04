import random
from locust import HttpUser, task, between

class RAGApiUser(HttpUser):
    # Simulates a user waiting 1 to 3 seconds between asking questions
    wait_time = between(1, 3)

    # Sample query pool to test performance under varying requests
    test_queries = [
        "What is the summary of the document?",
        "Solve the domain restriction formula f(x) = 1/(x-2)",
        "Explain the core methodology described in the paper.",
        "What is the value of x^2 + 5?",
        "Summarize the key findings briefly."
    ]

    @task
    def ask_rag_api(self):
        query_text = random.choice(self.test_queries)
        payload = {
            "query": query_text
        }
        headers = {"Content-Type": "application/json"}
        
        # Hits the FastAPI/Flask server endpoint (change /query to your API path if needed)
        self.client.post("/query", json=payload, headers=headers)