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
            "num_gpu": 99,
            "temperature": 0.1,
            "num_predict": 150,
            "num_ctx": 1024,
            "num_thread": 8,
            "repeat_penalty": 1.15
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
        """Check if Admin/Staff reviewed & corrected the answer for this question."""
        try:
            res = requests.get(
                "http://127.0.0.1:8000/feedback-correction",
                params={"question": query_text},
                timeout=0.3
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("found") and data.get("answer"):
                    print(f"✨ [FEEDBACK OVERRIDE]: Found corrected answer for question '{query_text}'")
                    return data.get("answer")
        except Exception as e:
            print(f"⚠️ [FEEDBACK CHECK FAILED]: {e}")
        return None

    def set_model(self, model_name: str):
        if self.model_name != model_name:
            print(f"[RAG] Switching LLM model from '{self.model_name}' to '{model_name}'")
            self.model_name = model_name
            self.llm = ChatOllama(
                model=self.model_name,
                **self.default_kwargs
            )

    def _get_context_and_docs(
        self,
        query,
        k=3
    ):
        try:
            docs = self.vectorstore.similarity_search(
                query,
                k=k
            )

            if not docs:
                print("[RAG] No matching documents found")
                return "", []

            print("=" * 50)
            print("QUESTION:", query)
            print("RETRIEVED DOCS COUNT:", len(docs))
            print("BEST DOC SAMPLE:")
            print(docs[0].page_content[:500])
            print("=" * 50)

            context_text = "\n\n".join(
                [doc.page_content for doc in docs]
            )

            return context_text, docs

        except Exception as e:
            print(f"[RAG] Retrieval Error: {e}")
            return "", []

    def _build_prompt(
        self,
        query,
        context_text
    ):
        query_lower = query.lower()
        math_keywords = [
            "solve", "calculate", "find", "evaluate", "integrate",
            "differentiate", "derivative", "integral", "equation",
            "matrix", "algebra", "calculus", "limit", "theorem", "proof"
        ]

        is_math = (
            any(keyword in query_lower for keyword in math_keywords)
            or any(symbol in query for symbol in ["=", "+", "-", "*", "/", "^", "²", "√", "(", ")"])
        )

        is_short = any(word in query_lower for word in ["short", "shortly", "in short", "summary", "quick"])
        is_brief = any(word in query_lower for word in ["brief", "briefly", "detail", "detailed", "elaborate", "explain"])

        if is_short:
            length_instruction = "Keep your answer very short, concise, and directly to the point (2-3 bullet points max)."
        elif is_brief:
            length_instruction = "Provide a clear, well-structured explanation using bullet points and a concise example."
        else:
            length_instruction = "Provide a clear, direct response with key points and a concise example."

        if is_math:
            return f"""You are Study AI Mathematics Tutor.
You provide clean, step-by-step textbook math solutions.

CRITICAL FORMATTING INSTRUCTIONS:
1. Put EVERY STEP on a SEPARATE NEW LINE.
2. Insert a BLANK LINE between every step.
3. NEVER output LaTeX commands (Do NOT write \\sqrt, \\frac, \\pm, \\infty, \\mathbb{{R}}, \\cdot, \\, \\[, \\], \\(, \\)).
4. Use ONLY clean Unicode symbols: √, ±, ∞, ℝ, ≥, ≤, ·, ², ³.

Follow this EXACT step-by-step layout:

Step 1: Rewrite as a quadratic in y
Given: 2x + 2xy + y² = 5
Rearrange: y² + 2xy + 2x - 5 = 0
Notice that: y² + 2xy = (y + x)² - x²
So: (y + x)² - x² + 2x - 5 = 0
(y + x)² = x² - 2x + 5
Thus: y + x = ±√(x² - 2x + 5)
Hence: y = -x ± √(x² - 2x + 5)

Step 2: Use the condition y > -x
Since y + x = ±√(x² - 2x + 5) and √(x² - 2x + 5) > 0,
the condition y > -x implies y + x > 0.
Therefore, choose the positive root:
f(x) = -x + √(x² - 2x + 5)

Step 3: Find the domain
The square root requires: x² - 2x + 5 ≥ 0
Complete the square: x² - 2x + 5 = (x - 1)² + 4
Since (x - 1)² ≥ 0 for all real x: (x - 1)² + 4 > 0 for every real x.
Therefore, the expression under the square root is always positive.
So there are no restrictions on x.
Domain of f is (-∞, ∞) = ℝ.

Final Answer:
The function is f(x) = -x + √(x² - 2x + 5)
and the domain of f is (-∞, ∞) = ℝ.

Verification (Optional):
Let y = -x + √(x² - 2x + 5). Then y + x = √(x² - 2x + 5).
Squaring both sides: (y + x)² = x² - 2x + 5 => y² + 2xy + x² = x² - 2x + 5 => 2x + 2xy + y² = 5.
Also y + x = √(x² - 2x + 5) > 0 => y > -x.
Hence the solution satisfies the given condition.

Rules:
- If question or document is missing from RAG, respond EXACTLY:
{FALLBACK_MESSAGE}

Context:
{context_text}

Question:
{query}

Answer:"""

        return f"""You are Study AI, an educational study assistant. Answer the user's question using ONLY the provided retrieved context.

CRITICAL INSTRUCTIONS:
1. If the user asks for a flow diagram, architecture, or workflow, construct a clear ASCII diagram using simple boxes and arrows based on the context (e.g., [ Nodes ] -> [ Weighted Edges ] -> [ Summation & Activation Function ] -> [ Output Neuron ]).
2. Do NOT say "Sorry, the provided document is not uploaded" if the concept or figure description is present in the context.
3. If the question or answer is NOT supported by the retrieved context, output ONLY:
{FALLBACK_MESSAGE}

Context:
{context_text}

Question:
{query}

Instructions:
1. Answer using ONLY the retrieved context.
2. {length_instruction}
3. Always include a relevant "Example:" section at the end of your answer.

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

        # Ensure headings like ### Step 1 start on a fresh line
        cleaned = re.sub(r'([^\n])\s*(###?\s*Step|\bStep\s+\d+:)', r'\1\n\n\2', cleaned)
        cleaned = re.sub(r'([^\n])\s*(\bFinal Answer:)', r'\1\n\n\2', cleaned)
        cleaned = re.sub(r'([^\n])\s*(\bVerification\b)', r'\1\n\n\2', cleaned)

        return cleaned

    def _is_query_supported_by_context(self, query: str, context_text: str) -> bool:
        """Verify if retrieved context contains relevant topic keywords from user query."""
        if not context_text or not context_text.strip():
            return False

        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "to", "from", "in", "out",
            "on", "off", "over", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all", "any", "both",
            "each", "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very", "can",
            "will", "just", "should", "now", "of", "and", "or", "give", "me",
            "what", "which", "find", "show", "tell", "explain", "defined"
        }

        import re
        query_words = set(re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', query.lower()))
        keywords = [w for w in query_words if w not in stop_words]

        if not keywords:
            return True

        context_lower = context_text.lower()
        matches = [w for w in keywords if w in context_lower]

        if not matches:
            print(f"[RAG] Key topic words {keywords} not found in retrieved context.")
            return False

        return True

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

        context_text, docs = self._get_context_and_docs(
            query_text,
            k=3
        )

        if not docs or not context_text.strip() or not self._is_query_supported_by_context(query_text, context_text):
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

            if not answer_text.strip() or "not available in the uploaded" in answer_text.lower() or "not uploaded" in answer_text.lower() or "sorry" in answer_text.lower()[:30]:
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
        query_text: str
    ) -> Generator[str, None, None]:
        print(f"[STREAM] Starting query_stream for: {query_text}")

        corrected = self._check_feedback_correction(query_text)
        if corrected:
            print(f"[STREAM] Feedback correction found, returning corrected answer")
            yield corrected
            return

        context_text, docs = self._get_context_and_docs(
            query_text,
            k=3
        )

        print(f"[STREAM] Docs found: {len(docs) if docs else 0}")
        print(f"[STREAM] Context length: {len(context_text) if context_text else 0}")

        if not docs or not context_text.strip():
            print(f"[STREAM] No docs or empty context -> fallback")
            yield FALLBACK_MESSAGE
            return

        if not self._is_query_supported_by_context(query_text, context_text):
            print(f"[STREAM] Keyword check failed -> fallback")
            yield FALLBACK_MESSAGE
            return

        print(f"[STREAM] Building prompt and starting LLM stream...")

        formatted_prompt = self._build_prompt(
            query_text,
            context_text
        )

        full_output = ""
        chunk_count = 0
        try:
            for chunk in self.llm.stream(formatted_prompt):
                chunk_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                full_output += chunk_text
                chunk_count += 1
                yield self._clean_formatting(chunk_text)

            print(f"[STREAM] LLM streaming complete: {chunk_count} chunks, {len(full_output)} chars")

        except Exception as e:
            print(f"[STREAM] Streaming error after {chunk_count} chunks: {e}")
            if not full_output.strip():
                yield FALLBACK_MESSAGE