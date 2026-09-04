from database.connection import SessionLocal
from database.models import ChatMessage


def save_message(
    session_id,
    sender,
    message
):

    db = SessionLocal()

    try:

        chat_message = ChatMessage(

            session_id=session_id,

            sender=sender,

            message=message

        )

        db.add(chat_message)

        db.commit()

        return {

            "status": True

        }

    finally:

        db.close()