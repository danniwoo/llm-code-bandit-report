from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
import os
import uuid
from PyPDF2 import PdfReader
from langchain.embeddings import OpenAIEmbeddings  # Or your preferred embedding model
from langchain.vectorstores import Chroma  # Or your chosen vector database
from langchain.docstore.document import Document

# --- Security Setup ---
security = HTTPBearer()
API_TOKEN = os.environ.get("API_TOKEN")  # Store your API token securely

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials

# --- Configuration ---
UPLOAD_FOLDER = "uploaded_pdfs"
VECTOR_DB_PATH = "vector_db"  # Consider making this configurable

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = FastAPI()

@app.post("/upload_pdf/")
async def upload_pdf(
    file: UploadFile = File(...),
    token: HTTPAuthorizationCredentials = Depends(verify_token)
):
    """
    Endpoint to upload a PDF file, process its content,
    generate embeddings, and store them in a vector database.
    Requires a valid API token for authentication.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    try:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")

        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # Read in chunks to handle large files
                f.write(chunk)

        # --- PDF Processing and Embedding ---
        text = ""
        try:
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            os.remove(file_path)  # Clean up uploaded file on processing error
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")

        if not text.strip():
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="PDF file is empty or contains no text.")

        embeddings = OpenAIEmbeddings()  # Initialize your embedding model
        documents = [Document(page_content=text, metadata={"file_id": file_id})]
        vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=VECTOR_DB_PATH)
        vectorstore.persist()

        os.remove(file_path)  # Clean up the original uploaded file

        return {"file_id": file_id, "message": "PDF uploaded and processed successfully."}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Log the error for debugging purposes (consider using a proper logging mechanism)
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload and processing.")