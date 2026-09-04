from database.connection import SessionLocal
from database.models import ChatSession


def save_chat(email, title):

    db = SessionLocal()

    try:

        chat = ChatSession(
            email=email,
            title=title
        )

        db.add(chat)

        db.commit()

        db.refresh(chat)

        return {
            "id": chat.id,
            "title": chat.title,
            "pinned": chat.pinned
        }

    finally:

        db.close()