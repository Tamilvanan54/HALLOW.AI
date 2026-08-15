from database.connection import SessionLocal
from database.models import User

from datetime import datetime


def verify_otp(email, otp):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            return {
                "status": False,
                "message": "User not found"
            }

        if user.reset_token != otp:
            return {
                "status": False,
                "message": "Invalid OTP"
            }

        if datetime.utcnow() > user.reset_expiry:
            return {
                "status": False,
                "message": "OTP Expired"
            }

        return {
            "status": True,
            "message": "OTP Verified"
        }

    finally:
        db.close()