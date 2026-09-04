from passlib.context import CryptContext

from database.connection import SessionLocal
from database.models import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

db = SessionLocal()

admin = db.query(User).filter(
    User.email == "admin@college.com"
).first()

if admin:

    print("Admin Already Exists")

else:

    new_admin = User(
        name="College Admin",
        email="esec.ac.in",
        password=pwd_context.hash("Admin@123"),
        role="admin"
    )

    db.add(new_admin)

    db.commit()

    print("Admin Created Successfully")