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
    role
):

    db = SessionLocal()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return {
            "status": False,
            "message": "User already exists"
        }

    # Role normalize
    role = role.lower()

    # Admin account creation block
    if role == "admin":
        return {
            "status": False,
            "message": "Admin account cannot be created"
        }

    # Allow only student and staff
    if role not in ["student", "staff"]:
        return {
            "status": False,
            "message": "Invalid role"
        }

    hashed_password = pwd_context.hash(
        password
    )

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    # Audit Log Entry
    write_log(
        "SIGNUP",
        email,
        role
    )

    return {
        "status": True,
        "message": "User Created Successfully"
    }