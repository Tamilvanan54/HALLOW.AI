import requests
from typing import Generator
from langchain_ollama import ChatOllama

FALLBACK_MESSAGE = "Sorry, I cannot find information regarding this question in the uploaded documents."

class RAGEngine:

    def __init__(
        self,
        vectorstore,
        model_name="qwen2.5:3b",
        model_kwargs=None
    ):
        self.vectorstore = vectorstore
        self.model_name = model_name

        self.options = {
            "num_gpu": 0,
            "temperature": 0.0,
            "num_predict": 200,
            "num_ctx": 384,
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

    def _check_feedback_correction(self, query_text: str) -> str | None:
        """Check if Admin/Staff reviewed & corrected the answer in feedback section FIRST."""
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
                    if ans and "cannot find information" not in ans.lower() and "sorry" not in ans.lower()[:20]:
                        print(f"✨ [FEEDBACK FIRST MATCH]: Found feedback answer for question '{query_text}'")
                        return ans
        except Exception:
            pass
        return None

    def set_model(self, model_name: str):
        if self.model_name == model_name and hasattr(self, "llm") and self.llm:
            return

        print(f"[RAG] Requesting model '{model_name}'")

        fast_options = dict(self.options)
        fast_options["num_ctx"] = 384
        fast_options["num_predict"] = 200
        fast_options["temperature"] = 0.0
        fast_options["top_k"] = 5
        fast_options["top_p"] = 0.5
        fast_options["num_gpu"] = 0

        fast_kwargs = dict(self.default_kwargs)
        fast_kwargs["options"] = fast_options
        fast_kwargs["keep_alive"] = "24h"

        candidate_models = [model_name]
        if "qwen" in model_name.lower():
            candidate_models.extend(["qwen2.5:1.5b", "qwen2.5:latest", "qwen2.5:7b", "qwen2.5", "qwen2.5:3b"])
        elif "llama" in model_name.lower():
            candidate_models.extend(["llama3.2:3b", "llama3.2:latest", "llama3.2:1b", "llama3.2", "llama3"])

        # Add general fallbacks
        for fallback in ["qwen2.5:1.5b", "qwen2.5:latest", "llama3.2:3b", "llama3.2"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        for candidate in candidate_models:
            try:
                print(f"[RAG] Initializing LLM with candidate model: '{candidate}'")
                llm_instance = ChatOllama(
                    model=candidate,
                    **fast_kwargs
                )
                self.llm = llm_instance
                self.model_name = candidate
                print(f"✅ [RAG] Successfully bound active LLM model: '{candidate}'")
                return
            except Exception as err:
                print(f"⚠️ [RAG] Candidate model '{candidate}' failed to load: {err}")

        # Final safety fallback
        self.model_name = model_name
        self.llm = ChatOllama(model=model_name, **fast_kwargs)

    def _get_context_and_docs(
        self,
        query,
        k=3
    ):
        try:
            is_math = self._classify_query(query)[0]
            # Math queries with equations need threshold 1.15 to capture formulas
            threshold = 1.15 if is_math else 0.92

            results = self.vectorstore.similarity_search_with_score(query, k=k)
            if not results:
                print("[RAG] No matching documents found")
                return "", []

            valid_docs = []
            for doc, score in results:
                print(f"[RAG] Query: '{query[:25]}' | Doc score: {score}")
                if score < threshold:
                    valid_docs.append(doc)

            if not valid_docs:
                print(f"[RAG] Question '{query[:30]}' is NOT in RAG documents -> returning empty context")
                return "", []

            # Math formulas need 700 chars context to capture complete step-by-step working
            context_limit = 700 if is_math else 380
            context_text = "\n\n".join(
                [doc.page_content for doc in valid_docs]
            )[:context_limit]

            return context_text, valid_docs

        except Exception as e:
            print(f"[RAG] Retrieval Error: {e}")
            return "", []

    def _classify_query(self, query: str):
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
            "in detail", "in-depth", "in depth", "elaborate", "explain in detail",
            "essay", "full explanation", "comprehensive", "long answer", "describe in detail"
        ]
        is_big = any(k in query_lower for k in big_keywords)

        diagram_keywords = [
            "flowchart", "flow chart", "diagram", "graph", "workflow",
            "architecture", "process", "pipeline", "tree", "chart"
        ]
        is_diagram = any(k in query_lower for k in diagram_keywords)

        return is_math, is_big, is_diagram

    def _build_prompt(
        self,
        query,
        context_text
    ):
        is_math, is_big, is_diagram = self._classify_query(query)

        if is_diagram:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Draw an ASCII diagram inside a code block, then explain briefly.
2. Leave a blank line, then write "Example:" followed by a practical example.

Answer:"""

        if is_math:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Solve step-by-step: Write Step 1:, Step 2:, Step 3: on separate lines with all working clearly shown.
2. Write "Final Answer:" on its own line.
3. Use clean Unicode math symbols (√, ±, ², ³, ·, ∫, ℝ) without raw LaTeX code.
4. Leave a blank line, then write "Example:" followed by a short verification example.

Solution:"""

        if is_big:
            return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Provide a detailed 16-mark answer (Definition, Key Points, Process).
2. Leave a blank line, then write "Example:" followed by a practical application example.

Answer:"""

        return f"""Context:
{context_text}

Question: {query}

Instructions:
1. Provide 3-4 lines of clear explanation based on the Context.
2. Leave a blank line, then write "Example:" followed by a practical real-world example.

Answer:"""

    def _clean_formatting(self, text: str) -> str:
        if not text:
            return ""

        import re

        # Regex replacements for LaTeX fractions and square roots
        cleaned = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
        cleaned = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', cleaned)
        cleaned = re.sub(r'\\sqrt\s*([a-zA-Z0-9]+)', r'√\1', cleaned)
        cleaned = re.sub(r'\\text\{([^}]+)\}', r'\1', cleaned)
        cleaned = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', cleaned)
        cleaned = re.sub(r'\\mathbf\{([^}]+)\}', r'\1', cleaned)

        # LaTeX symbols to Unicode map
        cleaned = (
            cleaned
            .replace("\\pm", "±")
            .replace("\\sqrt", "√")
            .replace("\\infty", "∞")
            .replace("\\int", "∫")
            .replace("\\partial", "∂")
            .replace("\\sum", "∑")
            .replace("\\prod", "∏")
            .replace("\\alpha", "α")
            .replace("\\beta", "β")
            .replace("\\theta", "θ")
            .replace("\\pi", "π")
            .replace("\\delta", "δ")
            .replace("\\in", "∈")
            .replace("\\notin", "∉")
            .replace("\\subset", "⊂")
            .replace("\\cup", "∪")
            .replace("\\cap", "∩")
            .replace("\\mathbb{R}", "ℝ")
            .replace("\\mathbb{Q}", "ℚ")
            .replace("\\mathbb{Z}", "ℤ")
            .replace("\\mathbb{N}", "ℕ")
            .replace("\\mathbb{C}", "ℂ")
            .replace("\\R", "ℝ")
            .replace("\\cdot", "·")
            .replace("\\times", "×")
            .replace("\\div", "÷")
            .replace("\\geq", "≥")
            .replace("\\leq", "≤")
            .replace("\\neq", "≠")
            .replace("\\approx", "≈")
            .replace("\\Rightarrow", "⇒")
            .replace("\\Leftrightarrow", "⇔")
            .replace("\\rightarrow", "→")
            .replace("\\leftarrow", "←")
            .replace("\\iff", "⇔")
            .replace("\\quad", " ")
            .replace("\\,", " ")
            .replace("\\;", " ")
            .replace("\\:", " ")
            .replace("\\(", "")
            .replace("\\)", "")
            .replace("\\[", "")
            .replace("\\]", "")
            .replace("^2", "²")
            .replace("^3", "³")
        )

        # Ensure headings like ### Step 1 and Example start on a fresh line with double spacing
        cleaned = re.sub(r'([^\n])\s*(###?\s*Step|\bStep\s+\d+:)', r'\1\n\n\2', cleaned)
        cleaned = re.sub(r'([^\n])\s*(\bFinal Answer:)', r'\1\n\n\2', cleaned)
        cleaned = re.sub(r'([^\n])\s*(\bVerification\b)', r'\1\n\n\2', cleaned)
        cleaned = re.sub(r'([^\n])\s*(\bExample:|\bExamples:)', r'\1\n\n\2', cleaned)

        return cleaned

    def _is_query_supported_by_context(self, query: str, context_text: str) -> bool:
        """Verify if retrieved context contains valid text."""
        return bool(context_text and context_text.strip())

    def query(
        self,
        query_text
    ):
        corrected = self._check_feedback_correction(query_text)
        if corrected:
            return {
                "answer": corrected,
                "context": []
            }

        is_math = self._classify_query(query_text)[0]
        k_value = 4 if is_math else 3

        context_text, docs = self._get_context_and_docs(
            query_text,
            k=k_value
        )

        if not docs or not context_text or not context_text.strip():
            return {
                "answer": FALLBACK_MESSAGE,
                "context": []
            }

        formatted_prompt = self._build_prompt(
            query_text,
            context_text
        )

        try:
            response = self.llm.invoke(formatted_prompt)
            answer_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            answer_text = self._clean_formatting(answer_text)

            if not answer_text.strip() or "not available in the uploaded" in answer_text.lower() or "not uploaded in the document" in answer_text.lower():
                answer_text = FALLBACK_MESSAGE

            return {
                "answer": answer_text,
                "context": docs
            }

        except Exception as e:
            print(f"[RAG] Query Error: {e}")
            return {
                "answer": FALLBACK_MESSAGE,
                "context": []
            }

    def query_stream(
        self,
        query_text: str,
        history: str | None = None
    ) -> Generator[str, None, None]:
        print(f"[STREAM] Starting query_stream for: {query_text}")

        corrected = self._check_feedback_correction(query_text)
        if corrected:
            print(f"[STREAM] Feedback correction found, returning corrected answer")
            yield corrected
            return

        is_math = self._classify_query(query_text)[0]
        k_value = 4 if is_math else 3

        # Include key terms from history if query is a short follow-up
        search_query = query_text
        if history and history.strip() and len(query_text.split()) < 5:
            user_lines = [line for line in history.split("\n") if line.startswith("User:")]
            if user_lines:
                search_query = f"{user_lines[-1].replace('User:', '').strip()} {query_text}"

        context_text, docs = self._get_context_and_docs(
            search_query,
            k=k_value
        )

        print(f"[STREAM] Docs found: {len(docs) if docs else 0}")
        print(f"[STREAM] Context length: {len(context_text) if context_text else 0}")

        if not docs or not context_text or not context_text.strip():
            print("[STREAM] No relevant documents found -> strictly returning fallback message")
            yield FALLBACK_MESSAGE
            return

        print(f"[STREAM] Building prompt and starting LLM stream...")

        formatted_prompt = self._build_prompt(
            query_text,
            context_text
        )

        if history and history.strip():
            formatted_prompt = f"Chat History:\n{history.strip()}\n\n" + formatted_prompt

        is_math, is_big, is_diagram = self._classify_query(query_text)
        if is_big:
            predict_tokens = 280
        elif is_math:
            predict_tokens = 220
        elif is_diagram:
            predict_tokens = 160
        else:
            predict_tokens = 160

        full_output = ""
        chunk_count = 0
        try:
            for chunk in self.llm.stream(formatted_prompt):
                chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                full_output += chunk_text
                chunk_count += 1
                yield chunk_text

            print(f"[STREAM] LLM streaming complete: {chunk_count} chunks, {len(full_output)} chars")

        except Exception as e:
            print(f"[STREAM] Primary model '{self.model_name}' streaming error: {e}")
            fallback_models = ["llama3.2:3b", "llama3.2", "qwen2.5:1.5b", "qwen2.5:latest", "qwen2.5:7b", "qwen2.5"]
            recovered = False
            for fb_model in fallback_models:
                if fb_model != self.model_name:
                    try:
                        print(f"[STREAM] Attempting fallback model: {fb_model}")
                        fb_llm = ChatOllama(
                            model=fb_model,
                            keep_alive="24h",
                            options={"num_ctx": 384, "num_predict": predict_tokens, "temperature": 0.0, "num_gpu": 0, "num_thread": 4}
                        )
                        for chunk in fb_llm.stream(formatted_prompt):
                            chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                            full_output += chunk_text
                            chunk_count += 1
                            yield chunk_text
                        recovered = True
                        print(f"[STREAM] Successfully recovered using model '{fb_model}'!")
                        break
                    except Exception as fb_err:
                        print(f"[STREAM] Fallback model '{fb_model}' failed: {fb_err}")
            if not recovered and not full_output.strip():
                yield FALLBACK_MESSAGE