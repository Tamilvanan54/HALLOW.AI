from database.connection import SessionLocal
from database.models import User


def get_all_users():

    db = SessionLocal()

    try:

        users = db.query(User).all()

        result = []

        for user in users:

            result.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            )

        return result

    finally:
        db.close()


def delete_user(user_id):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if not user:

            return {
                "status": False,
                "message": "User Not Found"
            }

        db.delete(user)

        db.commit()

        return {
            "status": True,
            "message": "User Deleted Successfully"
        }

    finally:
        db.close()