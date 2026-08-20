import os
import json
import re
import time
import requests
from typing import Generator
from langchain_ollama import ChatOllama
from app.abbreviations import expand_query_abbreviations
from app.spelling import correct_query_spelling
from app.history import resolve_history_reference

EXACT_REFUSAL_MESSAGE = "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question."
NO_EXAMPLE_FALLBACK = "### Example\nThe uploaded documents do not provide a specific example for this concept."

class RAGEngine:

    def __init__(
        self,
        vectorstore,
        model_name="qwen2.5:1.5b",
        model_kwargs=None
    ):
        self.vectorstore = vectorstore
        self.model_name = model_name
        self.pdf_vocabulary = set()

        self.options = {
            "num_gpu": 0,
            "temperature": 0.0,
            "num_predict": 220,
            "num_ctx": 256,
            "num_thread": 4,
            "repeat_penalty": 1.05,
            "top_k": 5,
            "top_p": 0.5
        }

        self.default_kwargs = {
            "keep_alive": "24h",
            "options": self.options
        }
        if model_kwargs:
            if "options" in model_kwargs:
                self.options.update(model_kwargs["options"])
            self.default_kwargs.update(model_kwargs)
            self.default_kwargs["options"] = self.options

        self.llm = ChatOllama(
            model=self.model_name,
            **self.default_kwargs
        )

    def set_model(self, model_name: str):
        if not model_name:
            return

        if hasattr(self, "llm") and self.llm:
            current_lower = self.model_name.lower()
            target_lower = model_name.lower()
            if ("qwen" in target_lower and "qwen" in current_lower) or ("llama" in target_lower and "llama" in current_lower):
                return

        print(f"[RAG] Requesting model switch to '{model_name}'")
        fast_options = dict(self.options)
        fast_options["num_ctx"] = 256
        fast_options["num_predict"] = 220
        fast_options["temperature"] = 0.0
        fast_options["top_k"] = 5
        fast_options["top_p"] = 0.5
        fast_options["num_gpu"] = 0

        fast_kwargs = dict(self.default_kwargs)
        fast_kwargs["options"] = fast_options
        fast_kwargs["keep_alive"] = "24h"

        candidate_models = ["qwen2.5:1.5b", "qwen2.5:0.5b", model_name]
        if "qwen" in model_name.lower():
            candidate_models.extend(["qwen2.5:1.5b", "qwen2.5:0.5b", "qwen2.5:latest", "qwen2.5:3b"])
        elif "llama" in model_name.lower():
            candidate_models.extend(["llama3.2:1b", "llama3.2:3b", "llama3.2:latest"])

        for candidate in candidate_models:
            try:
                print(f"[RAG] Initializing LLM candidate: '{candidate}'")
                llm_instance = ChatOllama(model=candidate, **fast_kwargs)
                self.llm = llm_instance
                self.model_name = candidate
                print(f"✅ [RAG] Successfully bound LLM model: '{candidate}'")
                return
            except Exception as err:
                print(f"⚠️ candidate '{candidate}' failed: {err}")

        self.model_name = model_name
        self.llm = ChatOllama(model=model_name, **fast_kwargs)

    def _check_feedback_correction(self, query_text: str) -> str | None:
        """Check if Admin/Staff reviewed & corrected answer in feedback section."""
        try:
            res = requests.get(
                "http://127.0.0.1:8000/feedback-correction",
                params={"question": query_text},
                timeout=0.015
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("found") and data.get("answer"):
                    ans = str(data.get("answer")).strip()
                    if ans and "cannot find information" not in ans.lower() and "study materials" not in ans.lower():
                        return ans
        except Exception:
            pass
        return None

    def _classify_query(self, query: str) -> tuple[bool, bool, bool]:
        query_lower = query.lower()

        math_keywords = [
            "solve", "calculate", "find", "evaluate", "integrate",
            "differentiate", "derivative", "integral", "equation",
            "matrix", "algebra", "calculus", "limit", "theorem", "proof",
            "domain", "formula", "roots", "quadratic", "sum", "multiply",
            "function", "f(x)", "y =", "x2y", "range", "inverse",
            "trigonometry", "sin", "cos", "tan", "log", "ln"
        ]
        is_math = (
            any(k in query_lower for k in math_keywords)
            or any(s in query for s in ["=", "+", "*", "/", "^", "²", "³", "√", "↔", "<->", "->"])
        )

        big_keywords = [
            "16 mark", "16-mark", "16mark", "10 mark", "10-mark", "10mark",
            "8 mark", "8-mark", "brief", "briefly", "big answer", "detail", "detailed",
            "in detail", "in-depth", "in depth", "elaborate", "essay", "full explanation"
        ]
        is_big = any(k in query_lower for k in big_keywords)

        diagram_keywords = [
            "flowchart", "flow chart", "diagram", "graph", "workflow",
            "architecture", "process", "pipeline", "tree", "chart"
        ]
        is_diagram = any(k in query_lower for k in diagram_keywords)

        return is_math, is_big, is_diagram

    def _get_context_and_docs(self, query: str, k: int = 4) -> tuple[str, list, list]:
        """
        Retrieve relevant chunks from vectorstore and apply configurable relevance threshold.
        Returns: (context_text, valid_docs, raw_sources_metadata)
        """
        try:
            is_math = self._classify_query(query)[0]
            env_thresh = float(os.getenv("RAG_RELEVANCE_THRESHOLD", "0.85"))
            env_math_thresh = float(os.getenv("RAG_MATH_THRESHOLD", "1.00"))
            threshold = env_math_thresh if is_math else env_thresh

            results = self.vectorstore.similarity_search_with_score(query, k=k)
            if not results:
                print(f"[RAG] Vectorstore empty or no matches for: '{query[:30]}'")
                return "", [], []

            valid_docs = []
            sources_metadata = []
            for doc, score in results:
                doc_name = doc.metadata.get("source", "study_material.pdf")
                doc_page = doc.metadata.get("page", 1)
                snippet = doc.page_content[:200]
                print(f"[RAG] Query: '{query[:25]}' | Doc: {doc_name} (P.{doc_page}) | Distance Score: {score:.4f}")

                # Reject chunks exceeding distance threshold
                if score < threshold:
                    valid_docs.append(doc)
                    sources_metadata.append({
                        "document": doc_name,
                        "page": doc_page,
                        "snippet": snippet,
                        "score": round(score, 4)
                    })

            if not valid_docs:
                print(f"[RAG] All retrieved chunks exceeded relevance threshold ({threshold}) for query: '{query[:30]}'")
                return "", [], []

            context_limit = 650 if is_math else 350
            context_text = "\n\n".join([doc.page_content for doc in valid_docs])[:context_limit]
            return context_text, valid_docs, sources_metadata

        except Exception as e:
            print(f"[RAG] Vector retrieval error: {e}")
            return "", [], []

    def _build_prompt(self, query: str, context_text: str) -> str:
        is_math, is_big, is_diagram = self._classify_query(query)

        if is_diagram:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Draw an ASCII diagram inside a code block, then explain briefly using ONLY Context.
2. Leave a blank line, then write "### Example" followed by an example from Context.

Answer:"""

        if is_math:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Solve step-by-step using ONLY the Context formulas:
### Step 1
...

### Step 2
...

### Final Answer
...

2. Leave a blank line, then write:
### Example
[Short verification example]

Use LaTeX notation for math (e.g. $x^2 + y^2$ or $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$).

Solution:"""

        if is_big:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Provide a detailed 16-mark answer (Definition, Key Points, Process) using ONLY Context.
2. Leave a blank line, then write "### Example" followed by an example.

Answer:"""

        return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Provide a concise 3-4 lines explanation based ONLY on the Context.
2. Leave a blank line, then write "### Example" followed by a practical example.

Answer:"""

    def _ensure_example_section(self, answer_text: str, context_text: str) -> str:
        """Ensure every valid grounded answer contains exactly ONE '### Example' section."""
        if not answer_text:
            return answer_text

        cleaned = answer_text.strip()
        # Deduplicate any repeated ### Example headers
        cleaned = re.sub(r'(?:\n*\s*###?\s*Example:?\s*)+', r'\n\n### Example\n', cleaned, flags=re.IGNORECASE)

        if "### Example" in cleaned:
            return cleaned.strip()

        # Check if context contains an example
        context_lower = context_text.lower() if context_text else ""
        if "example" in context_lower or "for instance" in context_lower or "such as" in context_lower:
            return f"{cleaned}\n\n### Example\nExample supported by uploaded document context."

        return f"{cleaned}\n\n{NO_EXAMPLE_FALLBACK}"

    def query_stream_sse(
        self,
        query_text: str,
        history: str | list | None = None
    ) -> Generator[str, None, None]:
        """
        SSE Generator yielding structured SSE events:
        - status: Searching uploaded study materials…
        - meta: corrected_query + sources
        - token: streamed text chunks
        - final: complete response metadata JSON
        """
        t_start = time.time()
        t_norm_start = time.time()

        # Step 1: Immediately stream status event (< 0.1s TTFT)
        yield 'event: status\ndata: {"message": "Searching uploaded study materials…"}\n\n'

        # Step 2: Normalize query and expand abbreviations
        expanded_query, is_ambiguous_abbr, abbr_clarification = expand_query_abbreviations(query_text, self.pdf_vocabulary)
        t_norm = round((time.time() - t_norm_start) * 1000, 2)

        if is_ambiguous_abbr and abbr_clarification:
            yield f'event: final\ndata: {{"answer": "{abbr_clarification}", "sources": [], "confidence": "clarification_needed", "refusal_reason": "ambiguous_abbreviation", "corrected_query": null, "timing_ms": {{"normalization": {t_norm}, "total": {t_norm}}}}}\n\n'
            return

        # Step 3: Conservative spelling correction
        t_spell_start = time.time()
        corrected_query, display_note = correct_query_spelling(expanded_query, self.pdf_vocabulary)
        t_spell = round((time.time() - t_spell_start) * 1000, 2)

        if display_note:
            yield f'event: meta\ndata: {{"corrected_query": "{corrected_query}", "display_note": "{display_note}"}}\n\n'

        # Step 4: Resolve chat history references
        search_query, is_unclear_ref, ref_reason, ref_clarification = resolve_history_reference(corrected_query, history)
        if is_unclear_ref and ref_clarification:
            yield f'event: final\ndata: {{"answer": "{ref_clarification}", "sources": [], "confidence": "clarification_needed", "refusal_reason": "{ref_reason}", "corrected_query": null, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
            return

        # Step 5: Check feedback correction first
        feedback_ans = self._check_feedback_correction(query_text)
        if feedback_ans:
            feedback_ans = self._ensure_example_section(feedback_ans, "")
            yield f'event: token\ndata: {{"token": {json.dumps(feedback_ans)}}}\n\n'
            yield f'event: final\ndata: {{"answer": {json.dumps(feedback_ans)}, "sources": [], "confidence": "grounded", "refusal_reason": null, "corrected_query": null, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
            return

        # Step 6: Vector search & relevance threshold validation
        t_ret_start = time.time()
        is_math = self._classify_query(corrected_query)[0]
        k_value = 4 if is_math else 3

        context_text, docs, sources_metadata = self._get_context_and_docs(search_query, k=k_value)
        t_ret = round((time.time() - t_ret_start) * 1000, 2)

        # STRICT REFUSAL: If no relevant chunks meet threshold, respond EXACTLY with required refusal message
        if not docs or not context_text or not context_text.strip():
            print(f"[RAG] Refusing query: '{query_text}' -> No chunks passed relevance threshold.")
            yield f'event: final\ndata: {{"answer": {json.dumps(EXACT_REFUSAL_MESSAGE)}, "sources": [], "confidence": "refused", "refusal_reason": "low_relevance", "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"normalization": {t_norm}, "typo_correction": {t_spell}, "retrieval": {t_ret}, "total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
            return

        # Send preliminary sources metadata
        yield f'event: meta\ndata: {{"sources": {json.dumps(sources_metadata)}, "corrected_query": {json.dumps(corrected_query if display_note else None)}}}\n\n'

        # Step 7: Build prompt and stream LLM tokens
        formatted_prompt = self._build_prompt(corrected_query, context_text)

        full_output = ""
        t_llm_first = None
        t_llm_start = time.time()

        try:
            for chunk in self.llm.stream(formatted_prompt):
                token = chunk.content if hasattr(chunk, "content") else str(chunk)
                if token:
                    if t_llm_first is None:
                        t_llm_first = round((time.time() - t_llm_start) * 1000, 2)
                    full_output += token
                    yield f'event: token\ndata: {{"token": {json.dumps(token)}}}\n\n'

            # Ensure answer includes Example section
            full_output = self._ensure_example_section(full_output, context_text)
            t_total = round((time.time() - t_start) * 1000, 2)

            yield f'event: final\ndata: {{"answer": {json.dumps(full_output)}, "sources": {json.dumps(sources_metadata)}, "confidence": "grounded", "refusal_reason": null, "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"normalization": {t_norm}, "typo_correction": {t_spell}, "retrieval": {t_ret}, "llm_first_token": {t_llm_first or 0}, "total": {t_total}}}}}\n\n'

        except Exception as err:
            print(f"⚠️ Streaming error: {err}")
            # Fallback refusal on stream exception
            yield f'event: final\ndata: {{"answer": {json.dumps(EXACT_REFUSAL_MESSAGE)}, "sources": [], "confidence": "refused", "refusal_reason": "llm_error", "corrected_query": null, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'