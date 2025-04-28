from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

app = FastAPI(title="WhatTheFridge API")

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Move the heavy import inside the function that uses it to enable lazy loading
# This helps reduce the cold start time and initial memory footprint
# from services.image_analysis import analyze_image

@app.get("/")
async def root():
    return {"message": "WhatTheFridge API is running"}

@app.get("/api")
async def api_root():
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
        # Lazy import to reduce cold start time
        from services.image_analysis import analyze_image
        
        contents = await image.read()
        results = analyze_image(contents)
        return results
    except Exception as e:
        error_msg = str(e)
        if "OpenAI API key is not set" in error_msg:
            raise HTTPException(status_code=500, detail="OpenAI API key is not configured. Please set OPENAI_API_KEY in the .env file.")
        else:
            print(f"Error analyzing image: {error_msg}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to analyze image: {error_msg}")

@app.post("/api/analyze-image")
async def api_analyze_fridge_image(image: UploadFile = File(...)):
    """Alternative endpoint for Vercel compatibility"""
    return await analyze_fridge_image(image)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True) 