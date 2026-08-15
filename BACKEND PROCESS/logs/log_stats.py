from database.connection import SessionLocal
from database.models import User, AuditLog


def get_login_stats():

    db = SessionLocal()

    try:

        total_users = db.query(
            User
        ).count()

        total_admins = db.query(
            User
        ).filter(
            User.role == "admin"
        ).count()

        total_students = db.query(
            User
        ).filter(
            User.role == "student"
        ).count()

        total_logins = db.query(
            AuditLog
        ).filter(
            AuditLog.action == "LOGIN"
        ).count()

        total_password_resets = db.query(
            AuditLog
        ).filter(
            AuditLog.action == "PASSWORD_RESET"
        ).count()

        latest_logs = db.query(
            AuditLog
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(20).all()

        logs_data = []

        for log in latest_logs:

            logs_data.append(
                {
                    "action": log.action,
                    "email": log.email,
                    "role": log.role,
                    "timestamp": str(
                        log.timestamp
                    )
                }
            )

        return {

            "status": True,

            "total_users":
                total_users,

            "total_admins":
                total_admins,

            "total_students":
                total_students,

            "total_logins":
                total_logins,

            "total_password_resets":
                total_password_resets,

            "recent_logs":
                logs_data
        }

    except Exception as e:

        return {
            "status": False,
            "message": str(e)
        }

    finally:

        db.close()