import os
import json

# Default Academic Abbreviation Dictionary
DEFAULT_ABBREVIATIONS = {
    "ML": "Machine Learning",
    "AI": "Artificial Intelligence",
    "DL": "Deep Learning",
    "NLP": "Natural Language Processing",
    "DBMS": "Database Management System",
    "OS": "Operating System",
    "CN": "Computer Networks",
    "SE": "Software Engineering",
    "OOP": "Object Oriented Programming",
    "DSA": "Data Structures and Algorithms",
    "DAA": "Design and Analysis of Algorithms",
    "TOC": "Theory of Computation",
    "CD": "Compiler Design",
    "COA": "Computer Organization and Architecture"
}

# Ambiguous abbreviations that may require context resolution or student clarification
AMBIGUOUS_ABBREVIATIONS = {
    "OS": ["Operating System", "Open Source"],
    "IP": ["Internet Protocol", "Intellectual Property"],
    "AI": ["Artificial Intelligence", "Appreciative Inquiry"]
}

def get_abbreviations_dict() -> dict[str, str]:
    """Load configurable abbreviation dictionary from environment or use defaults."""
    env_abbr = os.getenv("ABBREVIATIONS_DICT")
    if env_abbr:
        try:
            user_dict = json.loads(env_abbr)
            merged = dict(DEFAULT_ABBREVIATIONS)
            merged.update(user_dict)
            return merged
        except Exception as e:
            print(f"⚠️ Error parsing ABBREVIATIONS_DICT from env: {e}")
    return DEFAULT_ABBREVIATIONS

def expand_query_abbreviations(query: str, pdf_vocabulary: set | None = None) -> tuple[str, bool, str | None]:
    """
    Expand academic short forms in student queries.
    Returns: (expanded_query, is_ambiguous, clarification_prompt)
    """
    abbr_dict = get_abbreviations_dict()
    words = query.split()
    expanded_words = []
    has_ambiguity = False
    clarification_msg = None

    for i, word in enumerate(words):
        clean_word = word.strip(".,?!:;()[]{}").upper()
        
        # Check if word is an abbreviation
        if clean_word in abbr_dict:
            expansion = abbr_dict[clean_word]
            
            # Check for ambiguity if query context is vague (e.g. single word "What is OS?")
            if clean_word in AMBIGUOUS_ABBREVIATIONS and len(words) <= 3:
                possibilities = AMBIGUOUS_ABBREVIATIONS[clean_word]
                # If PDF vocabulary contains specific domain terms, resolve automatically
                if pdf_vocabulary:
                    matching = [p for p in possibilities if any(p.lower() in term.lower() for term in pdf_vocabulary)]
                    if len(matching) == 1:
                        expansion = matching[0]
                    elif len(matching) > 1 or not matching:
                        has_ambiguity = True
                        possibility_str = " or ".join(possibilities)
                        clarification_msg = f'Could you clarify what "{clean_word}" refers to? (e.g., {possibility_str}). I can then search the uploaded materials for the correct topic.'
                        expanded_words.append(word)
                        continue
                else:
                    has_ambiguity = True
                    possibility_str = " or ".join(possibilities)
                    clarification_msg = f'Could you clarify what "{clean_word}" refers to? (e.g., {possibility_str}). I can then search the uploaded materials for the correct topic.'
                    expanded_words.append(word)
                    continue

            expanded_words.append(expansion)
        else:
            expanded_words.append(word)

    expanded_query = " ".join(expanded_words)
    return expanded_query, has_ambiguity, clarification_msg
