from database.connection import SessionLocal
from database.models import AuditLog


def get_all_logs():

    db = SessionLocal()

    logs = db.query(AuditLog).all()

    result = []

    for log in logs:

        result.append(
            {
                "id": log.id,
                "action": log.action,
                "email": log.email,
                "role": log.role,
                "timestamp": str(log.timestamp)
            }
        )

    return result