import os
import sys
import json
import re
import time
import requests
from typing import Generator
from langchain_ollama import ChatOllama
from app.abbreviations import expand_query_abbreviations
from app.spelling import correct_query_spelling
from app.history import resolve_history_reference

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXACT_REFUSAL_MESSAGE = "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question."
NO_EXAMPLE_FALLBACK = "### Example\nThe uploaded documents do not provide a specific example for this concept."

def get_installed_ollama_models() -> list[str]:
    try:
        res = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", []) if m.get("name")]
            return models
    except Exception:
        pass
    return []

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
            "num_predict": 512,
            "num_ctx": 2048,
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

        # Initialize with installed model verification
        installed = get_installed_ollama_models()
        if installed and not any(model_name.lower() in m.lower() for m in installed):
            self.model_name = installed[0]
            print(f"[RAG] Default model '{model_name}' not in installed tags {installed}. Using '{self.model_name}'.")

        self.llm = ChatOllama(
            model=self.model_name,
            **self.default_kwargs
        )

    def set_model(self, model_name: str):
        if not model_name:
            return

        installed = get_installed_ollama_models()
        target_model = model_name

        if installed:
            req_lower = model_name.lower()
            matching = [m for m in installed if req_lower in m.lower() or m.lower() in req_lower]
            if matching:
                target_model = matching[0]
            else:
                target_model = installed[0]
                print(f"[RAG] Requested model '{model_name}' not downloaded in Ollama. Using available model '{target_model}'.")
        else:
            if "llama" in model_name.lower():
                target_model = "qwen2.5:1.5b"

        if hasattr(self, "llm") and self.llm and getattr(self, "model_name", "").lower() == target_model.lower():
            return

        print(f"[RAG] Binding LLM model: '{target_model}'")
        fast_options = dict(self.options)
        fast_options["num_ctx"] = 2048
        fast_options["num_predict"] = 512
        fast_options["temperature"] = 0.0
        fast_options["top_k"] = 5
        fast_options["top_p"] = 0.5
        fast_options["num_gpu"] = 0

        fast_kwargs = dict(self.default_kwargs)
        fast_kwargs["options"] = fast_options
        fast_kwargs["keep_alive"] = "24h"

        self.model_name = target_model
        self.llm = ChatOllama(model=target_model, **fast_kwargs)
        print(f"✅ [RAG] Successfully bound LLM model: '{target_model}'")

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
            "trigonometry", "sin", "cos", "tan", "log", "ln",
            "logic", "logical", "equivalence", "equivalences", "proposition",
            "propositional", "truth", "table", "statement", "quantifier",
            "predicates", "inference", "tautology", "contradiction"
        ]
        is_math = (
            any(k in query_lower for k in math_keywords)
            or any(s in query for s in ["=", "+", "*", "/", "^", "²", "³", "√", "↔", "<->", "->", "≡", "¬", "∧", "∨"])
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
        Retrieve relevant document chunks from vectorstore with strict similarity scoring & keyword matching.
        Returns: (context_text, valid_docs, raw_sources_metadata)
        """
        try:
            is_math = self._classify_query(query)[0]
            search_queries = [query]
            q_low = query.lower()
            if "logic" in q_low or "equivalen" in q_low or "table" in q_low:
                search_queries.append("logical equivalences laws identity commutative associative distributive de morgan tautology")

            # Extract non-stopword key topic words from query
            stop_words = {
                "what", "where", "who", "when", "why", "how", "tell", "explain",
                "does", "have", "with", "this", "that", "from", "your", "find",
                "give", "show", "is", "are", "was", "were", "the", "and", "for",
                "can", "you", "about", "which", "could", "would", "should", "some",
                "into", "than", "then", "them", "these", "those", "each", "every",
                "mean", "meant", "meaning", "define", "definition", "describe", "write",
                "list", "note", "short", "detail", "brief", "please", "answer"
            }
            raw_tokens = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', q_low)
            query_key_terms = [t for t in raw_tokens if t not in stop_words]

            results = []
            seen_contents = set()
            if self.vectorstore:
                for q in search_queries:
                    try:
                        # Use similarity_search_with_score to inspect L2 distance
                        q_docs_with_score = self.vectorstore.similarity_search_with_score(q, k=k)
                        for doc, score in q_docs_with_score:
                            if not doc.page_content or doc.page_content in seen_contents:
                                continue

                            # Score threshold: L2 distance in Chroma (>1.25 = weak / low similarity)
                            c_low = doc.page_content.lower()

                            # Keyword check if key terms exist
                            has_keyword_match = True
                            if query_key_terms:
                                has_keyword_match = any(t in c_low for t in query_key_terms)

                            # If no keyword match, require strong vector similarity (score <= 1.25)
                            # If keyword match exists, allow score up to 1.60
                            if not has_keyword_match and score > 1.25:
                                print(f"[RAG] Skipping weak chunk (score={score:.3f}, no keyword match): '{doc.page_content[:50]}...'")
                                continue
                            if score > 1.60:
                                print(f"[RAG] Skipping irrelevantly distant chunk (score={score:.3f}): '{doc.page_content[:50]}...'")
                                continue

                            seen_contents.add(doc.page_content)
                            results.append(doc)
                    except Exception as search_err:
                        print(f"⚠️ Vector search error for query '{q}': {search_err}")

            if not results and query_key_terms:
                print(f"[RAG] Vector search returned 0 strong matches for: '{query[:30]}'. Checking direct key term matches...")
                try:
                    import sys
                    rag_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    if rag_dir not in sys.path:
                        sys.path.insert(0, rag_dir)
                    from main import load_all_pdfs
                    all_chunks, _ = load_all_pdfs()
                    for chunk in all_chunks:
                        c_low = chunk.page_content.lower()
                        # Require at least one key term match
                        if any(term in c_low for term in query_key_terms):
                            if chunk.page_content not in seen_contents:
                                seen_contents.add(chunk.page_content)
                                results.append(chunk)
                                if len(results) >= k:
                                    break
                except Exception as fb_err:
                    print(f"⚠️ Direct PDF fallback note: {fb_err}")

            if not results:
                print(f"[RAG] No relevant document chunks found for: '{query[:30]}'")
                return "", [], []

            valid_docs = results[:k]
            sources_metadata = []
            for doc in valid_docs:
                doc_name = doc.metadata.get("source", "study_material.pdf")
                doc_page = doc.metadata.get("page", 1)
                snippet = doc.page_content[:200].replace('\n', ' ').replace('\r', '')
                sources_metadata.append({
                    "document": doc_name,
                    "page": doc_page,
                    "snippet": snippet,
                    "score": 1.0
                })

            print(f"[RAG] Retrieved {len(valid_docs)} relevant document chunks for query: '{query[:30]}'")
            context_limit = 1400 if is_math else 900
            context_text = "\n\n".join([doc.page_content for doc in valid_docs])[:context_limit]
            return context_text, valid_docs, sources_metadata

        except Exception as e:
            print(f"[RAG] Vector retrieval error: {e}")
            return "", [], []

    def _build_prompt(self, query: str, context_text: str) -> str:
        is_math, is_big, is_diagram = self._classify_query(query)

        strict_guardrail = """CRITICAL MANDATORY INSTRUCTION:
You are a strict document QA assistant. Answer the user's question ONLY and EXCLUSIVELY using the factual information provided in the Context below.

STRICT RULES:
1. If the Context does NOT contain enough relevant information to directly answer the question, or if the question asks about a topic not mentioned in the Context, you MUST respond with EXACTLY:
I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.
2. Do NOT use any outside knowledge, general world knowledge, or attempt to guess/invent an answer.
3. If the answer IS in the Context, explain it accurately based ONLY on the Context."""

        if is_diagram:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. {strict_guardrail}
2. Draw an ASCII diagram inside a code block, then explain briefly using ONLY Context.
3. Leave a blank line, then write "### Example" followed by an example from Context.

Answer:"""

        if is_math:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. {strict_guardrail}
2. Solve step-by-step using ONLY the Context formulas:
### Step 1
...

### Step 2
...

### Final Answer
...

3. Leave a blank line, then write:
### Example
[Short verification example]

Use LaTeX notation for math (e.g. $x^2 + y^2$ or $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$).

Solution:"""

        if is_big:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. {strict_guardrail}
2. Provide a detailed answer (Definition, Key Points, Process) using ONLY Context.
3. Leave a blank line, then write "### Example" followed by an example from Context.

Answer:"""

        return f"""Context:
{context_text}

Question: {query}

Instructions:
1. {strict_guardrail}
2. Provide 4-6 lines of clear explanation based ONLY on the Context.
3. Leave a blank line, then write "### Example" followed by a practical example from Context.

Answer:"""

    def _ensure_example_section(self, answer_text: str, context_text: str) -> str:
        """Ensure every valid grounded answer contains exactly ONE '### Example' section."""
        if not answer_text:
            return answer_text

        cleaned = answer_text.strip()
        if "can answer only from the uploaded study materials" in cleaned.lower() or EXACT_REFUSAL_MESSAGE.lower() in cleaned.lower():
            return EXACT_REFUSAL_MESSAGE

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

        # Step 7: Strict PDF context check
        if not docs or not context_text or not context_text.strip():
            print(f"[RAG] Question not present in uploaded study materials: '{query_text}'. Returning exact refusal message.")
            refusal_text = EXACT_REFUSAL_MESSAGE
            yield f'event: token\ndata: {{"token": {json.dumps(refusal_text)}}}\n\n'
            yield f'event: final\ndata: {{"answer": {json.dumps(refusal_text)}, "sources": [], "confidence": "refused", "refusal_reason": "not_in_study_materials", "corrected_query": null, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
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

            # Ensure answer includes Example section or exact refusal
            full_output = self._ensure_example_section(full_output, context_text)
            t_total = round((time.time() - t_start) * 1000, 2)

            is_refusal = (full_output == EXACT_REFUSAL_MESSAGE or "can answer only from the uploaded study materials" in full_output.lower())
            if is_refusal:
                full_output = EXACT_REFUSAL_MESSAGE
                yield f'event: final\ndata: {{"answer": {json.dumps(full_output)}, "sources": [], "confidence": "refused", "refusal_reason": "not_in_study_materials", "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"normalization": {t_norm}, "typo_correction": {t_spell}, "retrieval": {t_ret}, "llm_first_token": {t_llm_first or 0}, "total": {t_total}}}}}\n\n'
            else:
                yield f'event: final\ndata: {{"answer": {json.dumps(full_output)}, "sources": {json.dumps(sources_metadata)}, "confidence": "grounded", "refusal_reason": null, "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"normalization": {t_norm}, "typo_correction": {t_spell}, "retrieval": {t_ret}, "llm_first_token": {t_llm_first or 0}, "total": {t_total}}}}}\n\n'

        except Exception as err:
            print(f"⚠️ Streaming error with '{self.model_name}': {err}. Attempting fallback model stream...")
            try:
                fallback_model = "qwen2.5:1.5b"
                fallback_llm = ChatOllama(model=fallback_model, **self.default_kwargs)
                full_output = ""
                for chunk in fallback_llm.stream(formatted_prompt):
                    token = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if token:
                        full_output += token
                        yield f'event: token\ndata: {{"token": {json.dumps(token)}}}\n\n'

                full_output = self._ensure_example_section(full_output, context_text)
                is_refusal = (full_output == EXACT_REFUSAL_MESSAGE or "can answer only from the uploaded study materials" in full_output.lower())
                if is_refusal:
                    full_output = EXACT_REFUSAL_MESSAGE
                    yield f'event: final\ndata: {{"answer": {json.dumps(full_output)}, "sources": [], "confidence": "refused", "refusal_reason": "not_in_study_materials", "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
                else:
                    yield f'event: final\ndata: {{"answer": {json.dumps(full_output)}, "sources": {json.dumps(sources_metadata)}, "confidence": "grounded", "refusal_reason": null, "corrected_query": {json.dumps(corrected_query if display_note else None)}, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'
            except Exception as fb_err:
                print(f"❌ Fallback streaming error: {fb_err}")
                err_msg = EXACT_REFUSAL_MESSAGE
                yield f'event: token\ndata: {{"token": {json.dumps(err_msg)}}}\n\n'
                yield f'event: final\ndata: {{"answer": {json.dumps(err_msg)}, "sources": [], "confidence": "error", "refusal_reason": "llm_error", "corrected_query": null, "timing_ms": {{"total": {round((time.time() - t_start) * 1000, 2)}}}}}\n\n'