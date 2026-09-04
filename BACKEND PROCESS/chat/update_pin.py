from database.connection import SessionLocal
from database.models import ChatSession


def update_pin(chat_id):

    db = SessionLocal()

    try:

        chat = db.query(
            ChatSession
        ).filter(
            ChatSession.id == chat_id
        ).first()


        if not chat:

            return {
                "status":False,
                "message":"Chat Not Found"
            }


        if chat.pinned == "true":

            chat.pinned = "false"

        else:

            chat.pinned = "true"



        db.commit()


        return {

            "status":True,
            "pinned":chat.pinned

        }


    finally:

        db.close()