from database.connection import SessionLocal
from database.models import ChatSession
from database.models import ChatMessage


def delete_chat(chat_id):

    db = SessionLocal()

    try:

        db.query(
            ChatMessage
        ).filter(
            ChatMessage.session_id == chat_id
        ).delete()

        db.query(
            ChatSession
        ).filter(
            ChatSession.id == chat_id
        ).delete()

        db.commit()

        return {

            "status": True,

            "message":
            "Chat Deleted"

        }

    finally:

        db.close()