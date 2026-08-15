from database.connection import SessionLocal
from database.models import Feedback
from sqlalchemy import func

def get_corrected_answer(question: str):
    if not question:
        return {"found": False, "answer": None}

    db = SessionLocal()
    try:
        clean_q = question.strip().lower()

        # Query feedback with modified_answer present, ordered by newest first
        feedbacks = db.query(Feedback).filter(
            Feedback.modified_answer.isnot(None),
            Feedback.modified_answer != ""
        ).order_by(Feedback.id.desc()).all()

        matching_feedback = None
        for fb in feedbacks:
            if fb.question and fb.question.strip().lower() == clean_q:
                matching_feedback = fb
                break

        # Fallback substring / containment match if no exact match found
        if not matching_feedback:
            for fb in feedbacks:
                if fb.question and (fb.question.strip().lower() in clean_q or clean_q in fb.question.strip().lower()):
                    matching_feedback = fb
                    break

        if not matching_feedback:
            return {
                "found": False,
                "answer": None
            }

        return {
            "found": True,
            "answer": matching_feedback.modified_answer,
            "feedback_id": matching_feedback.id
        }

    finally:
        db.close()