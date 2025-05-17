from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from typing import List
import asyncio  # For potential asynchronous operations

# Assume you have a function to process the uploaded files in your RAG pipeline
# This is a placeholder - replace with your actual implementation
async def process_rag_pipeline(file_paths: List[str]):
    """
    Placeholder function to simulate processing files in the RAG pipeline.
    Replace this with your actual RAG pipeline logic.
    """
    print(f"Processing files: {file_paths}")
    # Simulate some asynchronous work
    await asyncio.sleep(5)
    print("File processing complete.")
    return {"status": "processing_complete", "files": file_paths}

app = FastAPI()

@app.post("/uploadfiles/")
async def upload_files(files: List[UploadFile], background_tasks: BackgroundTasks):
    """
    Endpoint to upload multiple files and trigger RAG pipeline processing.
    Utilizes BackgroundTasks for efficient handling of the processing.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    uploaded_file_paths = []
    for file in files:
        try:
            # Save the uploaded file temporarily to disk
            file_path = f"temp_uploads/{file.filename}"  # Consider a more robust path management
            with open(file_path, "wb") as f:
                while contents := await file.read(1024 * 1024):  # Read in chunks for efficiency
                    f.write(contents)
            uploaded_file_paths.append(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file '{file.filename}': {e}")
        finally:
            await file.close()

    # Use BackgroundTasks to avoid blocking the response
    background_tasks.add_task(process_rag_pipeline, uploaded_file_paths)

    return {"message": f"Successfully uploaded {len(files)} files. Processing started in the background."}

# Example of a simple status endpoint (optional)
# You'd need to implement a way to track the status of background tasks
# statuses = {}
#
# @app.get("/status/{task_id}")
# async def get_status(task_id: str):
#     if task_id in statuses:
#         return {"task_id": task_id, "status": statuses[task_id]}
#     raise HTTPException(status_code=404, detail="Task not found")

if __name__ == "__main__":
    import uvicorn
    import os

    # Ensure the temporary upload directory exists
    os.makedirs("temp_uploads", exist_ok=True)

    uvicorn.run(app, host="0.0.0.0", port=8000)