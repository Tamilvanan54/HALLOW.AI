from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)

from datetime import datetime

from database.connection import Base



# =========================
# USER TABLE
# =========================

class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    name = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(150),
        unique=True,
        nullable=False
    )


    password = Column(
        String(255),
        nullable=False
    )


    role = Column(
        String(20),
        nullable=False
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )



    # Last Login Time

    last_login = Column(
        DateTime,
        nullable=True
    )



    # OTP Store

    reset_token = Column(
        String(10),
        nullable=True
    )



    # OTP Expiry

    reset_expiry = Column(
        DateTime,
        nullable=True
    )







# =========================
# AUDIT LOG TABLE
# =========================


class AuditLog(Base):

    __tablename__ = "audit_logs"



    id = Column(
        Integer,
        primary_key=True,
        index=True
    )



    action = Column(
        String(50)
    )



    email = Column(
        String(100)
    )



    role = Column(
        String(50)
    )



    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )









# =========================
# FEEDBACK TABLE
# =========================


class Feedback(Base):

    __tablename__ = "feedback"



    id = Column(
        Integer,
        primary_key=True,
        index=True
    )



    # Student Question

    question = Column(
        String(5000),
        nullable=False
    )



    # AI Generated Answer

    answer = Column(
        String(10000),
        nullable=False
    )



    # Student Feedback

    feedback = Column(
        String(500),
        nullable=False
    )



    # Student Email / User

    reported_by = Column(
        String(150),
        nullable=False
    )



    # Pending / Reviewed

    status = Column(
        String(50),
        default="Pending"
    )



    # 🔥 ADMIN CORRECTED ANSWER

    modified_answer = Column(
        String(10000),
        nullable=True
    )



    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # =========================
# CHAT SESSION TABLE
# =========================

class ChatSession(Base):

    __tablename__ = "chat_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    email = Column(
        String(150),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    pinned = Column(
        String(10),
        default="false"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# =========================
# CHAT MESSAGE TABLE
# =========================

class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        Integer,
        nullable=False
    )

    sender = Column(
        String(50),
        nullable=False
    )

    message = Column(
        String(10000),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )