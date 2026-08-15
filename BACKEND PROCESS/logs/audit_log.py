from datetime import datetime

from database.connection import SessionLocal
from database.models import AuditLog


def write_log(
    action,
    email,
    role
):

    db = SessionLocal()

    try:

        log_entry = AuditLog(
            action=action,
            email=email,
            role=role
        )

        db.add(log_entry)

        db.commit()

        with open(
            "logs/audit.log",
            "a",
            encoding="utf-8"
        ) as log_file:

            log_file.write(
                f"{datetime.utcnow()} | "
                f"{action} | "
                f"{email} | "
                f"{role}\n"
            )

    except Exception as e:

        db.rollback()

        print(
            f"Audit Log Error: {e}"
        )

    finally:

        db.close()