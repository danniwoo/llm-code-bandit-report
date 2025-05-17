from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List

app = FastAPI()

@app.post("/upload_pdf")
async def upload_pdf(pdf_file: UploadFile):
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    try:
        contents = await pdf_file.read()
        # Here you would typically process the PDF content
        # For example, you might save it to a directory or
        # extract the text and store it in your vector database.
        print(f"Received file: {pdf_file.filename}, size: {len(contents)} bytes")

        # For now, let's just return a success message
        return {"filename": pdf_file.filename, "message": "PDF uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"There was an error uploading the file: {e}")