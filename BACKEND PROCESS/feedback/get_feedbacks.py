from database.connection import SessionLocal
from database.models import Feedback


def get_all_feedbacks():

    db = SessionLocal()

    try:

        feedbacks = db.query(
            Feedback
        ).order_by(
            Feedback.created_at.desc()
        ).all()

        result = []

        for item in feedbacks:

            result.append({

                "id": item.id,

                "question": item.question,

                "answer": item.answer,

                "feedback": item.feedback,

                "reported_by": item.reported_by,

                "status": item.status,

                "created_at": str(item.created_at)

            })

        return result

    finally:

        db.close()