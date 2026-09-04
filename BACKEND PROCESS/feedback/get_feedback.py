from database.connection import SessionLocal
from database.models import Feedback


def get_feedback(feedback_id):

    db = SessionLocal()

    try:

        feedback = db.query(
            Feedback
        ).filter(
            Feedback.id == feedback_id
        ).first()


        if not feedback:

            return {
                "status": False,
                "message": "Feedback Not Found"
            }


        return {

            "id": feedback.id,

            "question": feedback.question,

            "answer": feedback.answer,

            "feedback": feedback.feedback,

            "reported_by": feedback.reported_by,

            "status": feedback.status,

            "created_at": str(feedback.created_at)

        }


    finally:

        db.close()