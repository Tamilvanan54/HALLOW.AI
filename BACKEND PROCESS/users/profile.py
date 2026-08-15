from database.connection import SessionLocal
from database.models import User


def get_profile(email):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:

            return {
                "status": False,
                "message": "User Not Found"
            }

        return {

            "status": True,

            "id": user.id,

            "name": user.name,

            "email": user.email,

            "role": user.role,

            "created_at":
                str(user.created_at)
                if user.created_at
                else None,

            "last_login":
                str(user.last_login)
                if user.last_login
                else None

        }

    except Exception as e:

        return {

            "status": False,

            "message": str(e)

        }

    finally:

        db.close()