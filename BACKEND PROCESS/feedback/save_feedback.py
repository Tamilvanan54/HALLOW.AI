from database.connection import SessionLocal
from database.models import Feedback


def save_feedback(
    question,
    answer,
    feedback,
    reported_by
):

    db = SessionLocal()

    try:

        new_feedback = Feedback(
            question=question,
            answer=answer,
            feedback=feedback,
            reported_by=reported_by
        )

        db.add(new_feedback)

        db.commit()

        return {
            "status": True,
            "message": "Feedback Saved Successfully"
        }

    except Exception as e:

        db.rollback()

        return {
            "status": False,
            "message": str(e)
        }

    finally:

        db.close()


# ==========================
# GET ALL FEEDBACKS
# ==========================

def get_all_feedbacks():

    db = SessionLocal()

    try:

        feedbacks = db.query(
            Feedback
        ).order_by(
            Feedback.id.desc()
        ).all()

        return feedbacks

    finally:

        db.close()


# ==========================
# MARK AS REVIEWED
# ==========================

def mark_feedback_reviewed(
    feedback_id
):

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

        feedback.status = "Reviewed"

        db.commit()

        return {
            "status": True,
            "message": "Feedback Reviewed"
        }

    except Exception as e:

        db.rollback()

        return {
            "status": False,
            "message": str(e)
        }

    finally:

        db.close()