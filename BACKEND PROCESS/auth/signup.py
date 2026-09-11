from passlib.context import CryptContext

from database.connection import SessionLocal
from database.models import User

from logs.audit_log import write_log


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def create_user(
    name,
    email,
    password,
    role,
    college=None,
    department=None,
    year=None
):

    db = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            return {
                "status": False,
                "message": "User already exists with this email address!"
            }

        # Role normalize
        role = role.lower()

        # Admin account creation block
        if role == "admin":
            return {
                "status": False,
                "message": "Admin account cannot be created via signup."
            }

        # Allow only student and staff
        if role not in ["student", "staff"]:
            return {
                "status": False,
                "message": "Invalid role selected"
            }

        hashed_password = pwd_context.hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            college=college,
            department=department,
            year=year
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Audit Log Entry
        try:
            write_log(
                "SIGNUP",
                email,
                role
            )
        except Exception:
            pass

        return {
            "status": True,
            "message": "User Created Successfully"
        }

    except Exception as e:
        db.rollback()
        print(f"❌ SIGNUP ERROR: {e}")
        return {
            "status": False,
            "message": f"Signup error: {str(e)}"
        }
    finally:
        db.close()