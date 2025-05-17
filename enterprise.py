from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import os
from datetime import datetime

app = FastAPI()

UPLOAD_FOLDER = "uploaded_pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/pdfs/")
async def upload_pdfs(files: List[UploadFile]):
    """
    Endpoint to upload multiple PDF files.

    Args:
        files (List[UploadFile]): A list of uploaded PDF files.

    Returns:
        dict: A dictionary containing the status and details of the uploaded files.
    """
    uploaded_files = []
    failed_files = []

    for file in files:
        if file.content_type == "application/pdf":
            try:
                file_extension = os.path.splitext(file.filename)[1]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                with open(file_path, "wb") as f:
                    while contents := await file.read(1024 * 1024):  # Read in chunks
                        f.write(contents)

                uploaded_files.append({"filename": file.filename, "saved_as": unique_filename, "path": file_path})
            except Exception as e:
                failed_files.append({"filename": file.filename, "error": str(e)})
        else:
            failed_files.append({"filename": file.filename, "error": "Invalid file type. Only PDF files are allowed."})

    return {
        "status": "success" if not failed_files else "partial_failure",
        "uploaded": uploaded_files,
        "failed": failed_files,
    }