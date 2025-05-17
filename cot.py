from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from typing import List
import os
from werkzeug.utils import secure_filename
from pydantic import BaseModel
from datetime import datetime

# Assume you have a RAG system component
# For demonstration, we'll just define a placeholder
class RAGSystem:
    def ingest_pdf(self, file_path: str, original_filename: str, upload_timestamp: datetime):
        print(f"Placeholder: Ingesting PDF '{original_filename}' uploaded at {upload_timestamp} from {file_path} into RAG system.")

# Initialize FastAPI app
app = FastAPI()

# Placeholder for your RAG system instance
rag_system = RAGSystem()

# Define the upload folder (ensure it exists and has appropriate permissions)
UPLOAD_FOLDER = "rag_ingest_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define allowed file types
ALLOWED_EXTENSIONS = {"pdf"}

# Define maximum file size (in bytes - e.g., 10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

class UploadResponse(BaseModel):
    filename: str
    message: str
    upload_timestamp: datetime

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(upload_file: UploadFile, destination_folder: str) -> str:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base, ext = os.path.splitext(secure_filename(upload_file.filename))
        unique_filename = f"{base}_{timestamp}{ext}"
        file_path = os.path.join(destination_folder, unique_filename)
        with open(file_path, "wb") as f:
            while chunk := upload_file.file.read(1024 * 1024):  # Read in chunks
                f.write(chunk)
        return file_path, upload_file.filename, datetime.now()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    finally:
        upload_file.file.close()

@app.post("/upload_pdf/", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(..., max_length=MAX_FILE_SIZE)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are allowed."
        )
    if len(await file.read()) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail=f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB."
        )
    await file.seek(0)  # Reset file pointer after reading for size check

    try:
        file_path, original_filename, upload_timestamp = save_uploaded_file(file, UPLOAD_FOLDER)
        rag_system.ingest_pdf(file_path, original_filename, upload_timestamp)
        return UploadResponse(filename=original_filename, message="PDF file uploaded and being processed.", upload_timestamp=upload_timestamp)
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)