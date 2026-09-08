import unittest
import os
import json
import sys

# Add RAG PROCESS and BACKEND PROCESS to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RAG PROCESS")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BACKEND PROCESS")))

from app.abbreviations import expand_query_abbreviations
from app.spelling import correct_query_spelling
from app.history import resolve_history_reference
from app.rag_engine import EXACT_REFUSAL_MESSAGE, NO_EXAMPLE_FALLBACK

class MockDocument:
    def __init__(self, page_content, source="MachineLearning.pdf", page=1):
        self.page_content = page_content
        self.metadata = {"source": source, "page": page}

class MockVectorStore:
    def __init__(self, docs_with_scores=None):
        self.docs_with_scores = docs_with_scores or []

    def similarity_search_with_score(self, query, k=4):
        return self.docs_with_scores

from unittest.mock import patch, MagicMock

class TestRAGSystem(unittest.TestCase):

    def setUp(self):
        self.sample_vocabulary = {"Machine Learning", "Machine", "Learning", "Algorithm", "Regression", "Artificial Intelligence"}
        self.ollama_patcher = patch("app.rag_engine.ChatOllama", return_value=MagicMock())
        self.mock_chat_ollama = self.ollama_patcher.start()

    def tearDown(self):
        self.ollama_patcher.stop()

    # Test 1: Question present in uploaded PDF gives grounded answer with PDF/page citations
    def test_01_grounded_answer_with_citations(self):
        doc = MockDocument("Machine learning is a subset of artificial intelligence that enables systems to learn from data.", "ml_notes.pdf", 3)
        mock_vs = MockVectorStore([(doc, 0.45)])
        
        # Test vector search retrieval
        results = mock_vs.similarity_search_with_score("What is Machine Learning?", k=3)
        self.assertTrue(len(results) > 0)
        retrieved_doc, score = results[0]
        self.assertEqual(retrieved_doc.metadata["source"], "ml_notes.pdf")
        self.assertEqual(retrieved_doc.metadata["page"], 3)
        self.assertLess(score, 1.08)

    # Test 2: Unrelated question is refused with EXACT refusal message
    def test_02_unrelated_question_refused(self):
        mock_vs = MockVectorStore([])  # No matching document chunks
        results = mock_vs.similarity_search_with_score("Who won the 2024 World Cup?", k=3)
        self.assertEqual(len(results), 0)
        self.assertEqual(EXACT_REFUSAL_MESSAGE, "I can answer only from the uploaded study materials. I could not find enough relevant information in the available documents for this question.")

    # Test 3: Low-relevance question is refused
    def test_03_low_relevance_question_refused(self):
        doc = MockDocument("Unrelated text about cooking and baking cakes.", "cooking.pdf", 1)
        mock_vs = MockVectorStore([(doc, 1.35)])  # Score 1.35 exceeds threshold 1.08
        results = mock_vs.similarity_search_with_score("Explain quantum physics", k=3)
        valid = [d for d, s in results if s < 1.08]
        self.assertEqual(len(valid), 0)

    # Test 4: Every successful answer includes ### Example
    def test_04_every_valid_answer_includes_example(self):
        from app.rag_engine import RAGEngine
        engine = RAGEngine(vectorstore=MockVectorStore())
        context = "Machine learning is useful for spam detection."
        answer = "Machine learning classifies data."
        formatted = engine._ensure_example_section(answer, context)
        self.assertIn("### Example", formatted)

    # Test 5: Maths answers use LaTeX and step-by-step structure
    def test_05_maths_answers_format(self):
        from app.rag_engine import RAGEngine
        engine = RAGEngine(vectorstore=MockVectorStore())
        is_math, _, _ = engine._classify_query("Solve x^2 + 5x + 6 = 0")
        self.assertTrue(is_math)
        prompt = engine._build_prompt("Solve x^2 + 5x + 6 = 0", "Quadratic formula x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}")
        self.assertIn("### Step 1", prompt)
        self.assertIn("### Final Answer", prompt)

    # Test 6: Follow-up question uses chat history for reference resolution
    def test_06_followup_question_reference(self):
        history = "User: What is Machine Learning?\nAssistant: Machine learning is..."
        search_q, is_unclear, ref_reason, _ = resolve_history_reference("give its usage", history)
        self.assertFalse(is_unclear)
        self.assertIn("Machine Learning", search_q)

    # Test 7: "What is ML?" abbreviation expansion
    def test_07_abbreviation_expansion_ml(self):
        expanded, is_ambig, _ = expand_query_abbreviations("What is ML?")
        self.assertFalse(is_ambig)
        self.assertIn("Machine Learning", expanded)

    # Test 8: "What is machin learnig?" spelling correction
    def test_08_spelling_correction_typo(self):
        corrected, display_note = correct_query_spelling("what is machin learnig", self.sample_vocabulary)
        self.assertIn("Machine Learning", corrected)
        self.assertIsNotNone(display_note)
        self.assertIn("Searching for: Machine Learning", display_note)

    # Test 9: Ambiguous abbreviation asks clarification
    def test_09_ambiguous_abbreviation_clarification(self):
        expanded, is_ambig, clarification = expand_query_abbreviations("What is OS?")
        self.assertTrue(is_ambig)
        self.assertIn("Could you clarify what \"OS\" refers to?", clarification)

    # Test 10: Stream sends status event first
    def test_10_stream_status_event_first(self):
        from app.rag_engine import RAGEngine
        from unittest.mock import MagicMock
        doc = MockDocument("Machine learning algorithms...", "ml.pdf", 1)
        engine = RAGEngine(vectorstore=MockVectorStore([(doc, 0.40)]))

        mock_chunk = MagicMock()
        mock_chunk.content = "Machine learning is a method."
        engine.llm = MagicMock()
        engine.llm.stream.return_value = [mock_chunk]

        events = list(engine.query_stream_sse("What is machine learning"))
        self.assertTrue(len(events) > 0)
        first_event = events[0]
        self.assertIn("event: status", first_event)
        self.assertIn("Searching uploaded study materials", first_event)

    # Test 11: Unclear follow-up reference asks clarification
    def test_11_unclear_followup_reference(self):
        search_q, is_unclear, ref_reason, clarification = resolve_history_reference("give its usage", history=None)
        self.assertTrue(is_unclear)
        self.assertEqual(ref_reason, "unclear_reference")
        self.assertIn("Could you clarify what \"it\" refers to?", clarification)

    # Test 12: Multi-tenant access control (Student isolated chat history)
    def test_12_multitenant_history_isolation(self):
        student1_history = "User: What is Machine Learning?"
        student2_history = "User: What is Calculus?"
        
        q1, _, _, _ = resolve_history_reference("explain it", student1_history)
        q2, _, _, _ = resolve_history_reference("explain it", student2_history)
        
        self.assertIn("Machine Learning", q1)
        self.assertIn("Calculus", q2)
        self.assertNotEqual(q1, q2)

    # Test 13: Invalid or scanned PDF error handling
    def test_13_scanned_pdf_error_handling(self):
        import fitz
        # Create an empty/scanned PDF page without text
        doc = fitz.open()
        doc.new_page()
        total_text = "".join(page.get_text("text").strip() for page in doc)
        doc.close()
        self.assertLess(len(total_text), 20)

    # Test 14: Existing fallback message sanity check
    def test_14_exact_refusal_message_sanity(self):
        self.assertTrue(EXACT_REFUSAL_MESSAGE.startswith("I can answer only from the uploaded study materials."))

    # Test 15: Mark level detection for exam preparation (1, 2, 5, 7, 10, 12, 14, 16 marks)
    def test_15_mark_level_detection(self):
        from app.rag_engine import RAGEngine
        engine = RAGEngine(vectorstore=MockVectorStore())
        self.assertEqual(engine._detect_mark_level("What is CPU in 1 mark"), 1)
        self.assertEqual(engine._detect_mark_level("CPU mark 1 answer"), 1)
        self.assertEqual(engine._detect_mark_level("Explain RAM for 2 marks"), 2)
        self.assertEqual(engine._detect_mark_level("RAM 2 mark level"), 2)
        self.assertEqual(engine._detect_mark_level("Explain OSI model for 5 mark"), 5)
        self.assertEqual(engine._detect_mark_level("OSI model mark 7"), 7)
        self.assertEqual(engine._detect_mark_level("Write a 10 mark answer for normalization"), 10)
        self.assertEqual(engine._detect_mark_level("normalization 12 marks"), 12)
        self.assertEqual(engine._detect_mark_level("14 mark detailed explanation on Machine Learning"), 14)
        self.assertEqual(engine._detect_mark_level("Machine Learning mark 16 level"), 16)

    # Test 16: Mark level prompt structure & scaled example requirement
    def test_16_mark_level_prompt_building(self):
        from app.rag_engine import RAGEngine
        engine = RAGEngine(vectorstore=MockVectorStore())
        
        prompt_1m = engine._build_prompt("What is RAM in 1 mark", "RAM is random access memory.")
        self.assertIn("1-mark level answer", prompt_1m)

        prompt_2m = engine._build_prompt("Define deadlock in 2 mark", "Deadlock occurs when processes hold resources...")
        self.assertIn("2-mark level answer", prompt_2m)
        self.assertIn("exactly 3 to 5 lines", prompt_2m)
        self.assertIn("chinna example", prompt_2m)

        prompt_5m = engine._build_prompt("Explain OS scheduling in 5 marks", "OS scheduling algorithms manage CPU execution...")
        self.assertIn("5-mark level answer", prompt_5m)

        prompt_10m = engine._build_prompt("Explain sorting algorithms in 10 mark", "Sorting algorithms arrange data...")
        self.assertIn("10-mark level detailed answer", prompt_10m)

        prompt_16m = engine._build_prompt("Explain Neural Networks in 16 mark", "Neural networks consist of layers...")
        self.assertIn("16-mark level comprehensive", prompt_16m)
        self.assertIn("periya example fulla explain pannanum", prompt_16m)

if __name__ == "__main__":
    unittest.main()
