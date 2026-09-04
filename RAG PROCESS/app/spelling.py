import re
import difflib

# Common English stop words to ignore during typo correction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "in", "on", "at", "to", "for", "with",
    "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "in", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just",
    "don", "should", "now", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "give", "tell", "explain",
    "define", "list", "usages", "usage", "example", "examples", "step", "steps"
}

def extract_pdf_vocabulary(documents: list) -> set[str]:
    """Extract vocabulary terms (words and 2-3 word phrases) from PDF documents."""
    vocab = set()
    for doc in documents:
        text = doc.page_content if hasattr(doc, "page_content") else str(doc)
        # Extract clean words
        words = re.findall(r'\b[A-Za-z]{3,25}\b', text)
        for w in words:
            vocab.add(w)
            vocab.add(w.lower())
            vocab.add(w.capitalize())

        # Extract multi-word title/heading terms (e.g. "Machine Learning", "Neural Network")
        title_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        for phrase in title_phrases:
            vocab.add(phrase)
    return vocab

def correct_query_spelling(query: str, vocabulary: set[str]) -> tuple[str, str | None]:
    """
    Conservative spelling correction using PDF vocabulary.
    Returns: (corrected_query, display_note)
    Example: ("machin learnig") -> ("Machine Learning", "Searching for: Machine Learning")
    """
    if not query or not vocabulary:
        return query, None

    # Common explicit typos mapping for fast matching
    common_typo_map = {
        "machin learnig": "Machine Learning",
        "machin learning": "Machine Learning",
        "machine learnig": "Machine Learning",
        "artifical intellegence": "Artificial Intelligence",
        "artificial intellegence": "Artificial Intelligence",
        "artifical intelligence": "Artificial Intelligence",
        "algoritham": "algorithm",
        "neural netwrok": "neural network",
        "deep learnig": "Deep Learning"
    }

    query_lower = query.lower().strip()
    for typo, correction in common_typo_map.items():
        if typo in query_lower:
            corrected_query = re.sub(re.escape(typo), correction, query, flags=re.IGNORECASE)
            display_note = f"Searching for: {correction}"
            return corrected_query, display_note

    words = query.split()
    corrected_words = []
    corrections_made = []

    # Get lowercased vocabulary list for difflib matching
    vocab_list = [v for v in vocabulary if len(v) >= 3]

    for word in words:
        clean_word = re.sub(r'[^a-zA-Z]', '', word)
        clean_word_lower = clean_word.lower()

        # Skip short words or stop words
        if len(clean_word) < 4 or clean_word_lower in STOP_WORDS:
            corrected_words.append(word)
            continue

        # If word is already in vocabulary, keep it
        if clean_word_lower in [v.lower() for v in vocab_list]:
            corrected_words.append(word)
            continue

        # Find close matches in PDF vocabulary
        matches = difflib.get_close_matches(clean_word_lower, [v.lower() for v in vocab_list], n=1, cutoff=0.78)
        if matches:
            matched_vocab = matches[0]
            # Preserve original casing from vocabulary if available
            proper_match = next((v for v in vocabulary if v.lower() == matched_vocab), matched_vocab)
            # Replace clean_word in word
            new_word = word.replace(clean_word, proper_match)
            corrected_words.append(new_word)
            if proper_match.lower() != clean_word_lower:
                corrections_made.append(proper_match)
        else:
            corrected_words.append(word)

    corrected_query = " ".join(corrected_words)
    display_note = None
    if corrections_made and corrected_query.lower() != query.lower():
        display_note = f"Searching for: {' '.join(corrections_made)}"

    return corrected_query, display_note
