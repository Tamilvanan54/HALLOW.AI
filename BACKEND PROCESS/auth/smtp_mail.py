import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Replace with your Gmail
EMAIL_ADDRESS = "studyai2028@gmail.com"

# Replace with App Password
EMAIL_PASSWORD = "znjqfkvzojbsyiur"


def send_otp_email(
    receiver_email,
    otp
):

    try:

        subject = "Study AI Password Reset OTP"

        body = f"""
Hello,

Your Study AI Password Reset OTP is:

{otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

Thanks,
Study AI Team
"""

        msg = MIMEMultipart()

        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "plain"
            )
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_ADDRESS,
            receiver_email,
            msg.as_string()
        )

        server.quit()

        print(
            f"OTP Email Sent Successfully -> {receiver_email}"
        )

        return True

    except Exception as e:

        print(
            f"SMTP ERROR: {str(e)}"
        )

        return False