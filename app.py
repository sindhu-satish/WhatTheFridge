from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from services.image_analysis import analyze_image_with_openai
import os
import shutil
from datetime import datetime
import uuid

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

@app.get("/api")
async def health_check():
    return {"status": "healthy", "message": "WhatTheFridge API is running"}

@app.post("/api/analyze-image")
async def analyze_image(image: UploadFile = File(...)):
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = os.path.splitext(image.filename)[1]
        filename = f"{timestamp}_{unique_id}{file_extension}"
        file_path = os.path.join(IMAGES_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        with open(file_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        result = analyze_image_with_openai(image_bytes)
        
        result["image_path"] = file_path
        
        return JSONResponse(content=result)
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="UI/dist", html=True), name="ui") 