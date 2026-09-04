from database.connection import SessionLocal
from database.models import User, Feedback
import os


def collect_metrics():

    db = SessionLocal()

    try:

        total_users = db.query(
            User
        ).count()

        total_feedbacks = db.query(
            Feedback
        ).count()

        total_pdfs = len(
            os.listdir("uploads")
        )

        return {

            "total_users":
            total_users,

            "total_feedbacks":
            total_feedbacks,

            "total_pdfs":
            total_pdfs

        }

    finally:

        db.close()