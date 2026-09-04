from passlib.context import CryptContext

from database.connection import SessionLocal
from database.models import User

from auth.jwt import create_access_token

from logs.audit_log import write_log

from datetime import datetime
import pytz


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def login_user(
    email,
    password
):

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

        password_match = pwd_context.verify(
            password,
            user.password
        )

        if not password_match:

            return {
                "status": False,
                "message": "Invalid Password"
            }

        # Indian Time (IST)
        ist = pytz.timezone(
            "Asia/Kolkata"
        )

        user.last_login = datetime.now(
            ist
        )

        db.commit()

        token = create_access_token(
            {
                "email": user.email,
                "role": user.role
            }
        )

        write_log(
            "LOGIN",
            user.email,
            user.role
        )

        return {

            "status": True,

            "message":
                "Login Successful",

            "token":
                token,

            "role":
                user.role,

            "email":
                user.email,

            "last_login":
                str(user.last_login)

        }

    except Exception as e:

        db.rollback()

        return {

            "status": False,

            "message":
                str(e)

        }

    finally:

        db.close()