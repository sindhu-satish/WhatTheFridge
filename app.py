from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from services.image_analysis import analyze_image
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="WhatTheFridge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "WhatTheFridge API is running"}

@app.post("/analyze-image")
async def analyze_fridge_image(image: UploadFile = File(...)):
    """
    Analyze an uploaded image to identify food ingredients and their quantities.
    
    Args:
        image: The uploaded image file of a fridge or food items
        
    Returns:
        A dictionary containing the detected ingredients and their estimated quantities
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")
    
    try:
        contents = await image.read()
        results = analyze_image(contents)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 