from auth.smtp_mail import send_otp_email

from database.connection import SessionLocal
from database.models import User

from datetime import datetime, timedelta

from auth.otp import generate_otp


def forgot_password(email):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            return {
                "status": False,
                "message": "Email not found"
            }

        # Generate OTP
        otp = generate_otp()

        # Save OTP in DB
        user.reset_token = otp

        user.reset_expiry = (
            datetime.utcnow()
            + timedelta(minutes=5)
        )

        db.commit()

        # Send OTP to Gmail
        send_otp_email(
            email,
            otp
        )

        return {
            "status": True,
            "message": "OTP Sent To Email"
        }

    except Exception as e:

        db.rollback()

        return {
            "status": False,
            "message": str(e)
        }

    finally:
        db.close()