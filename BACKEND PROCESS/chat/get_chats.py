from database.connection import SessionLocal
from database.models import ChatSession


def get_chats(email):

    db = SessionLocal()

    try:

        chats = db.query(
            ChatSession
        ).filter(
            ChatSession.email == email
        ).order_by(
            ChatSession.id.desc()
        ).all()

        result = []

        for chat in chats:

            result.append({

                "id": chat.id,

                "title": chat.title,

                "pinned": chat.pinned

            })

        return result

    finally:

        db.close()