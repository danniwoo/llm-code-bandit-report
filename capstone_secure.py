from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import os
from pathlib import Path
import hashlib

app = FastAPI()
bearer_scheme = HTTPBearer()

# --- Configuration ---
UPLOAD_DIR = Path("./uploaded_pdfs")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = ["application/pdf"]
# In a real application, store this securely (e.g., environment variable)
API_TOKEN = "your_super_secret_api_token"

# Ensure the upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Security Dependency ---
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme")
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials

# --- Endpoint for Single File Upload ---
@app.post("/upload/pdf", dependencies=[Depends(verify_token)])
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    if await file.read(1) == b'':  # Check if the file is empty
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    await file.seek(0)  # Reset file pointer after peeking

    file_size = 0
    while chunk := await file.read(1024):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB.")
        # You might want to perform more robust content validation here if needed

    await file.seek(0)  # Reset file pointer before saving

    # Generate a secure filename using a hash of the content
    file_content = await file.read()
    filename_hash = hashlib.sha256(file_content).hexdigest()
    file_extension = ".pdf"
    secure_filename = f"{filename_hash}{file_extension}"
    file_path = UPLOAD_DIR / secure_filename

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    finally:
        await file.close()

    return {"filename": secure_filename, "message": f"File '{file.filename}' uploaded successfully as '{secure_filename}'"}

# --- Endpoint for Multiple File Uploads ---
@app.post("/upload/pdfs", dependencies=[Depends(verify_token)])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid file type for '{file.filename}'. Only PDF files are allowed.")

        if await file.read(1) == b'':
            raise HTTPException(status_code=400, detail=f"Uploaded file '{file.filename}' is empty.")
        await file.seek(0)

        file_size = 0
        while chunk := await file.read(1024):
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail=f"File size for '{file.filename}' exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB.")

        await file.seek(0)

        file_content = await file.read()
        filename_hash = hashlib.sha256(file_content).hexdigest()
        file_extension = ".pdf"
        secure_filename = f"{filename_hash}{file_extension}"
        file_path = UPLOAD_DIR / secure_filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            uploaded_files.append({"original_filename": file.filename, "stored_filename": secure_filename})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file '{file.filename}': {e}")
        finally:
            await file.close()

    return {"uploaded": uploaded_files, "message": f"{len(uploaded_files)} file(s) uploaded successfully."}