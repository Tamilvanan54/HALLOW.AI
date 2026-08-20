import re

REFERENCE_PRONOUNS = {"it", "its", "that", "their", "this", "them", "these", "those"}
FOLLOWUP_PHRASES = [
    "give its usage", "give its usages", "how it works", "how does it work",
    "explain step 2", "give more details", "tell me more", "what about it",
    "its applications", "usages of it", "give 3 examples", "what is its domain"
]

def resolve_history_reference(
    query: str,
    history: str | list | None
) -> tuple[str, bool, str | None, str | None]:
    """
    Resolve references like 'it', 'its', 'that' using persistent chat history.
    Returns: (search_query, is_unclear, refusal_type, clarification_message)
    """
    if not query:
        return query, False, None, None

    query_lower = query.lower().strip()
    words = set(query_lower.split())
    has_pronoun = bool(words.intersection(REFERENCE_PRONOUNS))
    has_followup_phrase = any(phrase in query_lower for phrase in FOLLOWUP_PHRASES)

    is_followup = has_pronoun or has_followup_phrase

    # If query does NOT need reference resolution, return original query
    if not is_followup:
        return query, False, None, None

    # Format history turns into list of strings
    history_lines = []
    if history:
        if isinstance(history, list):
            for turn in history:
                if isinstance(turn, dict):
                    sender = turn.get("sender", "User")
                    text = turn.get("text", "")
                    history_lines.append(f"{sender}: {text}")
                elif isinstance(turn, str):
                    history_lines.append(turn)
        elif isinstance(history, str):
            history_lines = [l.strip() for l in history.split("\n") if l.strip()]

    # Extract user questions from history
    user_questions = []
    for line in history_lines:
        if line.startswith("User:") or line.startswith("student:"):
            q_text = line.split(":", 1)[1].strip()
            # Ignore fallback answers or generic phrases
            if q_text and "cannot find information" not in q_text.lower():
                user_questions.append(q_text)

    # If query is a follow-up ("give its usages") but NO prior user topic exists in history:
    if is_followup and not user_questions:
        # Check if the pronoun is explicit
        if has_pronoun or "its" in query_lower or "it" in words:
            refusal_msg = 'Could you clarify what "it" refers to? I can then search the uploaded materials for the correct topic.'
            return query, True, "unclear_reference", refusal_msg

    # Extract previous user topic
    if user_questions:
        last_user_q = user_questions[-1][:80]
        # Avoid duplicating exact query
        if last_user_q.lower() != query_lower:
            search_query = f"{last_user_q} {query}"
            return search_query, False, None, None

    return query, False, None, None
