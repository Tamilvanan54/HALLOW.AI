import os
import sys
import warnings
from dotenv import load_dotenv
from datasets import Dataset

# Suppress non-critical warnings during evaluation
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# LangSmith Tracer
from langchain_core.tracers.context import tracing_v2_enabled

# Your RAG Engine
from app.rag_engine import RAGEngine

load_dotenv()


def run_evaluation(engine: RAGEngine = None):
    """Main evaluation routine callable from main.py or run directly as a script."""
    print("🚀 Starting Ragas + LangSmith Evaluation Run...")

    # Lazy imports to suppress startup warnings
    RAGAS_METRICS_READY = False
    try:
        from ragas import evaluate
        from ragas.metrics import (
            AnswerRelevancy,
            ContextPrecision,
            ContextRecall,
            Faithfulness,
        )
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_ollama import OllamaLLM, OllamaEmbeddings
        RAGAS_METRICS_READY = True
    except Exception as err:
        print(f"⚠️ Note: Ragas evaluators loaded in compatibility mode. ({err})")

    test_questions = [
        "What is Artificial Intelligence?",
        "What is Machine Learning?",
        "What is the difference between AI and Machine Learning?",
        "Explain Neural Networks.",
        "What are the applications of Artificial Intelligence?",
        "What is Calculus?",
        "Explain Derivatives.",
        "Explain Integration.",
        "What is the difference between differentiation and integration?",
        "What are the applications of Calculus?",
        "What is DBMS?",
        "Explain the advantages of DBMS.",
        "What is an Operating System?",
        "What are the functions of an Operating System?",
        "Explain Python Lists.",
        "Compare DBMS and File Management System.",
        "Compare Stack and Queue.",
        "Explain the difference between Python List and Tuple.",
        "What are the advantages of Machine Learning?",
        "Summarize the fundamental concepts of Artificial Intelligence.",
    ]

    ground_truths = [
        "Artificial Intelligence (AI) refers to computer systems designed to perform human-like cognitive tasks.",
        "Machine Learning is a subset of AI focused on systems that learn from data without explicit programming.",
        "AI is the broader concept of smart machines; ML is a subfield where machines learn directly from data.",
        "Neural networks are computing models inspired by biological human brains used to recognize patterns.",
        "AI applications include computer vision, speech recognition, NLP, robotics, and recommendation systems.",
        "Calculus is the branch of mathematics that studies continuous change through derivatives and integrals.",
        "Derivatives represent the instantaneous rate of change of a function with respect to a variable.",
        "Integration is the process of calculating area under a curve, representing accumulation of quantities.",
        "Differentiation measures rates of change; integration measures accumulated amounts under curves.",
        "Calculus is applied in physics, engineering, economics, machine learning optimization, and statistics.",
        "A Database Management System (DBMS) is software used to define, store, manage, and retrieve data.",
        "DBMS offers data integrity, security, concurrency control, data independence, and reduced redundancy.",
        "An Operating System (OS) is core software managing computer hardware resources and providing services.",
        "Functions of an OS include memory management, process scheduling, file system control, and device handling.",
        "Python lists are ordered, mutable, heterogenous collections defined using square brackets.",
        "DBMS provides structured data, security, and multi-user access; File systems offer basic hierarchical storage.",
        "A Stack follows Last-In-First-Out (LIFO); a Queue follows First-In-First-Out (FIFO).",
        "Lists are mutable and defined with square brackets; Tuples are immutable and defined with parentheses.",
        "ML advantages include automated decision making, continuous improvement from new data, and pattern discovery.",
        "Key concepts of AI include learning, reasoning, problem-solving, perception, and natural language processing.",
    ]

    if engine is None:
        print("[Setup]: Instantiating standalone RAGEngine...")
        engine = RAGEngine()

    answers = []
    contexts = []

    print(f"\n⏳ Fetching RAG responses for {len(test_questions)} test questions...")
    project_name = os.getenv("LANGCHAIN_PROJECT", "RAG_EVAL_SESSION")

    # Trace all calls into LangSmith automatically
    with tracing_v2_enabled(project_name=project_name):
        for idx, q in enumerate(test_questions, 1):
            print(f" [{idx}/{len(test_questions)}] Processing query: '{q}'")
            try:
                response = engine.query(q)

                if isinstance(response, dict):
                    ans = response.get("answer", response.get("result", str(response)))
                    docs = response.get("source_documents", response.get("context", []))
                else:
                    ans = str(response)
                    docs = []

                answers.append(ans)

                if isinstance(docs, list) and len(docs) > 0 and hasattr(docs[0], "page_content"):
                    chunk_texts = [doc.page_content for doc in docs]
                elif isinstance(docs, list):
                    chunk_texts = [str(d) for d in docs]
                else:
                    chunk_texts = [str(docs)]

                contexts.append(chunk_texts)

            except Exception as e:
                print(f"⚠️ Error on query '{q}': {e}")
                answers.append("Error generating response.")
                contexts.append(["No context retrieved."])

    raw_data = {
        "question": test_questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }

    eval_dataset = Dataset.from_dict(raw_data)

    # Execute Ragas Metrics if fully supported in environment
    if RAGAS_METRICS_READY:
        print("\n📊 Computing Ragas Metrics...")
        try:
            eval_llm = LangchainLLMWrapper(
                OllamaLLM(model="qwen2.5:1.5b", temperature=0.0)
            )
            eval_embeddings = LangchainEmbeddingsWrapper(
                OllamaEmbeddings(model="nomic-embed-text")
            )

            metrics = [
                Faithfulness(llm=eval_llm),
                AnswerRelevancy(llm=eval_llm, embeddings=eval_embeddings),
                ContextPrecision(llm=eval_llm),
                ContextRecall(llm=eval_llm),
            ]

            results = evaluate(dataset=eval_dataset, metrics=metrics)
            print("\n================ EVALUATION SUMMARY ================")
            print(results)
            print("=====================================================")
            df = results.to_pandas()
            df.to_csv("eval_results.csv", index=False)
            print("💾 Saved evaluation results to 'eval_results.csv'")
            return
        except Exception as e:
            print(f"\n⚠️ Ragas computation failed: {e}")

    # Default Export (Saves dataset + traces to LangSmith)
    df = eval_dataset.to_pandas()
    df.to_csv("eval_results_raw.csv", index=False)
    print("\n💾 Evaluation completed! Dataset saved to 'eval_results_raw.csv' and logged to LangSmith.")


if __name__ == "__main__":
    run_evaluation()