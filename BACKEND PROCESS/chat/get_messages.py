from database.connection import SessionLocal
from database.models import ChatMessage


def get_messages(
    session_id
):

    db = SessionLocal()

    try:

        messages = db.query(
            ChatMessage
        ).filter(
            ChatMessage.session_id == session_id
        ).all()

        result = []

        for msg in messages:

            result.append({

                "sender": msg.sender,

                "text": msg.message

            })

        return result

    finally:

        db.close()