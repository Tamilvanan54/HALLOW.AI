from database.connection import SessionLocal
from database.models import User

from passlib.context import CryptContext

from datetime import datetime

from logs.audit_log import write_log

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def reset_password(
    token,
    new_password
):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.reset_token == token
        ).first()

        if not user:
            return {
                "status": False,
                "message": "Invalid Token"
            }

        if (
            user.reset_expiry is None
            or user.reset_expiry < datetime.utcnow()
        ):
            return {
                "status": False,
                "message": "Token Expired"
            }

        hashed_password = pwd_context.hash(
            new_password
        )

        user.password = hashed_password

        # Clear OTP
        user.reset_token = None
        user.reset_expiry = None

        db.commit()

        # Audit Log
        write_log(
            "PASSWORD_RESET",
            user.email,
            user.role
        )

        return {
            "status": True,
            "message": "Password Reset Success"
        }

    except Exception as e:

        db.rollback()

        return {
            "status": False,
            "message": str(e)
        }

    finally:
        db.close()