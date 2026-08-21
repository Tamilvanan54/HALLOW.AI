from fastapi import FastAPI
from fastapi import UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from fastapi.responses import FileResponse

from monitoring.monitoring_controller import monitoring_dashboard
from data_governance.governance_controller import get_policies

from auth.signup import create_user
from auth.login import login_user

from auth.forgot_password import forgot_password
from auth.reset_password import reset_password

from chat.update_pin import update_pin

from chat.save_chat import save_chat
from chat.get_chats import get_chats
from chat.delete_chat import delete_chat

from rag.rag_client import ask_rag

from chat.save_message import save_message
from chat.get_messages import get_messages

from feedback.get_feedback import get_feedback
from feedback.save_feedback import save_feedback
from feedback.get_feedbacks import get_all_feedbacks
from feedback.update_feedback import update_feedback_status

from feedback.correction import get_corrected_answer

from users.profile import get_profile
from users.user import (
    get_all_users,
    delete_user
)


from logs.log_stats import get_login_stats


from pdf.delete_pdf import delete_pdf


import os
import requests




app = FastAPI()






# ==========================
# FEEDBACK UPDATE MODEL
# ==========================


class FeedbackUpdate(BaseModel):

    modified_answer: str | None = None

    status: str | None = None


class ChatRequest(BaseModel):

    question: str







# ==========================
# CORS
# ==========================


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)







# ==========================
# HOME
# ==========================


@app.get("/")
def home():


    return {


        "message":

        "College AI Backend Running"


    }







# ==========================
# SIGNUP
# ==========================


@app.post("/signup")
def signup(

    name: str,

    email: str,

    password: str,

    role: str

):


    return create_user(

        name,

        email,

        password,

        role

    )







# ==========================
# LOGIN
# ==========================


@app.post("/login")
def login(

    email: str,

    password: str

):


    return login_user(

        email,

        password

    )








# ==========================
# FORGOT PASSWORD
# ==========================


@app.post("/forgot-password")
def forgot(

    email: str

):


    return forgot_password(

        email

    )








# ==========================
# RESET PASSWORD
# ==========================


@app.post("/reset-password")
def reset(

    token: str,

    new_password: str

):


    return reset_password(

        token,

        new_password

    )








# ==========================
# PROFILE
# ==========================


@app.get("/profile")
def profile(

    email: str

):


    return get_profile(

        email

    )





# ==========================
# USERS
# ==========================


@app.get("/users")
def users():


    return get_all_users()







# ==========================
# DELETE USER
# ==========================


@app.delete("/delete-user/{user_id}")
def remove_user(

    user_id:int

):


    return delete_user(

        user_id

    )







# ==========================
# LOGS
# ==========================


@app.get("/logs")
def logs():


    return get_login_stats()


# ==========================
# MONITORING
# ==========================

@app.get("/monitoring")
def monitoring():

    return monitoring_dashboard()


# ==========================
# DATA GOVERNANCE
# ==========================

@app.get("/governance")
def governance():

    return get_policies()

# ==========================
# SAVE FEEDBACK
# ==========================


@app.post("/feedback")
def feedback(

    question:str,

    answer:str,

    feedback:str,

    reported_by:str

):


    return save_feedback(

        question,

        answer,

        feedback,

        reported_by

    )







# ==========================
# GET ALL FEEDBACKS
# ==========================


@app.get("/feedbacks")
def feedbacks():


    return get_all_feedbacks()







# ==========================
# GET SINGLE FEEDBACK
# ==========================


@app.get("/feedbacks/{feedback_id}")
def single_feedback(

    feedback_id:int

):


    return get_feedback(

        feedback_id

    )








# ==========================
# UPDATE FEEDBACK
# ==========================


@app.put("/feedbacks/{feedback_id}")
def update_feedback(

    feedback_id:int,

    data:FeedbackUpdate

):


    return update_feedback_status(

        feedback_id,

        data.modified_answer

    )









# ==========================
# PDF UPLOAD
# ==========================


@app.post("/upload-pdf")
async def upload_pdf(
    pdf: UploadFile = File(...)
):
    import fitz  # PyMuPDF
    import re

    page_count = 0
    safe_filename = "document.pdf"

    try:
        # 1. File extension validation
        if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
            return {
                "status": False,
                "message": "Invalid file type. Only PDF documents (.pdf) are allowed.",
                "filename": pdf.filename
            }

        # 2. Filename sanitization
        safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', os.path.basename(pdf.filename))

        content = await pdf.read()

        # 3. File size validation (Max 50MB)
        if len(content) == 0:
            return {
                "status": False,
                "message": "The uploaded PDF file is empty (0 bytes).",
                "filename": safe_filename
            }
        if len(content) > 50 * 1024 * 1024:
            return {
                "status": False,
                "message": "File size exceeds the 50MB limit.",
                "filename": safe_filename
            }

        # 4. Scanned & digital PDF check - accept all readable PDF documents
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            page_count = len(doc)
            doc.close()
            print(f"ℹ️ PDF accepted: {safe_filename} ({page_count} pages)")
        except Exception as e:
            print(f"⚠️ PDF inspection note: {e}")

        if not os.path.exists("uploads"):
            os.makedirs("uploads")

        file_path = f"uploads/{safe_filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        print(f"✅ Saved to backend uploads: {os.path.abspath(file_path)}")

        # Save directly to RAG PROCESS data folder
        backend_dir = os.path.abspath(os.path.dirname(__file__))
        rag_data_dir = os.path.abspath(os.path.join(backend_dir, "..", "RAG PROCESS", "data"))

        if not os.path.exists(rag_data_dir):
            os.makedirs(rag_data_dir)

        rag_file_path = os.path.join(rag_data_dir, safe_filename)
        try:
            with open(rag_file_path, "wb") as rag_buffer:
                rag_buffer.write(content)
            print(f"✅ Saved to RAG data: {rag_file_path}")
        except Exception as e:
            print(f"❌ Failed to save to RAG data: {e}")

        # Trigger ingest on RAG service asynchronously
        def _trigger_rag_ingest(fname: str):
            try:
                print(f"⏳ Calling RAG ingest for {fname}...")
                resp = requests.post(
                    "http://127.0.0.1:8001/api/ingest",
                    json={"filename": fname},
                    timeout=300
                )
                if resp.status_code == 200:
                    print(f"✅ RAG ingest success for {fname}: {resp.json()}")
                else:
                    print(f"⚠️ RAG ingest response: {resp.status_code} {resp.text}")
            except Exception as e:
                print(f"⚠️ RAG ingest background error for {fname}: {e}")

        import threading
        threading.Thread(target=_trigger_rag_ingest, args=(safe_filename,), daemon=True).start()

        return {
            "status": True,
            "message": "PDF Uploaded successfully! Processing into study materials.",
            "filename": safe_filename,
            "pages": page_count,
            "ingested": True
        }

    except Exception as exc:
        print(f"❌ upload_pdf exception: {exc}")
        return {
            "status": False,
            "message": f"Upload processing error: {str(exc)}",
            "filename": safe_filename
        }







# ==========================
# GET PDFS
# ==========================


@app.get("/pdfs")
def get_pdfs():


    if not os.path.exists("uploads"):


        os.makedirs("uploads")



    files = os.listdir("uploads")



    pdf_files=[


        file


        for file in files


        if file.endswith(".pdf")


    ]



    return {


        "status":True,


        "files":pdf_files


    }


# ==========================
# FEEDBACK CORRECTION API
# ==========================

@app.get("/feedback-correction")
def feedback_correction(

    question: str

):

    return get_corrected_answer(

        question

    )





# ==========================
# DELETE PDF
# ==========================


@app.delete("/delete-pdf")
def remove_pdf(
    filename: str
):
    res = delete_pdf(filename)
    try:
        requests.post(
            "http://127.0.0.1:8001/api/delete-doc",
            json={"filename": filename},
            timeout=10
        )
    except Exception as e:
        print(f"Failed to trigger RAG doc deletion: {e}")
    return res
# ==========================
# VIEW PDF
# ==========================

@app.get("/view-pdf/{filename}")
def view_pdf(filename: str):

    file_path = f"uploads/{filename}"

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )




# ===== CHAT ENDPOINTS =====

@app.post("/save-chat")
def create_chat(
    email: str,
    title: str
):

    return save_chat(
        email,
        title
    )


@app.get("/get-chats")
def load_chats(
    email: str
):

    return get_chats(
        email
    )


@app.delete("/delete-chat")
def remove_chat(
    chat_id: int
):

    return delete_chat(
        chat_id
    )


@app.post("/save-message")
def create_message(

    session_id: int,

    sender: str,

    message: str

):

    return save_message(

        session_id,

        sender,

        message

    )


@app.get("/get-messages")
def load_messages(
    session_id: int
):

    return get_messages(
        session_id
    )

@app.put("/pin-chat")
def pin_chat(
    chat_id:int
):

    return update_pin(
        chat_id
    )

# ==========================
# RAG CHAT
# ==========================

class ChatRequest(BaseModel):

    question: str


@app.post("/chat")
def chat(data: ChatRequest):

    return ask_rag(
        data.question
    )