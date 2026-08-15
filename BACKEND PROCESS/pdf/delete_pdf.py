import os

def delete_pdf(filename):
    file_path = f"uploads/{filename}"
    rag_data_path = os.path.join(os.path.dirname(__file__), "..", "..", "RAG PROCESS", "data", filename)

    deleted_any = False

    if os.path.exists(file_path):
        os.remove(file_path)
        deleted_any = True

    if os.path.exists(rag_data_path):
        os.remove(rag_data_path)
        deleted_any = True

    if not deleted_any:
        return {
            "status": False,
            "message": "File Not Found"
        }

    return {
        "status": True,
        "message": "PDF Deleted Successfully"
    }