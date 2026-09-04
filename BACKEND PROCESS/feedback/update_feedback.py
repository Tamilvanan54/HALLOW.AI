from database.connection import SessionLocal
from database.models import Feedback




def update_feedback_status(

    feedback_id,

    modified_answer=None

):


    db = SessionLocal()



    try:



        feedback = db.query(

            Feedback

        ).filter(

            Feedback.id == feedback_id

        ).first()





        if not feedback:



            return {


                "status": False,


                "message": "Feedback Not Found"


            }





        # ==========================
        # UPDATE STATUS
        # ==========================


        feedback.status = "Reviewed"






        # ==========================
        # SAVE ADMIN CORRECTION
        # ==========================


        if modified_answer is not None:


            feedback.modified_answer = modified_answer






        db.commit()





        db.refresh(

            feedback

        )







        return {



            "status": True,



            "message":

            "Feedback Updated Successfully",



            "feedback": {


                "id":

                feedback.id,


                "question":

                feedback.question,


                "old_answer":

                feedback.answer,


                "modified_answer":

                feedback.modified_answer,


                "feedback":

                feedback.feedback,


                "status":

                feedback.status


            }


        }






    except Exception as e:



        db.rollback()



        return {


            "status": False,


            "message":

            "Update Failed",


            "error":

            str(e)


        }







    finally:



        db.close()