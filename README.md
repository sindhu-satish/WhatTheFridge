# WhatTheFridge - AI Ingredient Detection API

This backend API uses computer vision AI models to identify ingredients in fridge images and estimate their quantities.

## Features

- Image upload endpoint to analyze fridge contents
- Advanced ingredient detection with specific quantity estimates (e.g., "3 apples", "500ml milk")
- Object counting for discrete items (e.g., fruits, eggs)
- Depth estimation for more accurate volume/weight measurement of continuous items (cheese, liquids)
- Support for both local models and OpenAI Vision API
- Configurable model selection

## Technology Stack

- FastAPI for the API framework
- Hugging Face Transformers for local AI models
- MiDaS for monocular depth estimation
- Optional integration with OpenAI's GPT-4 Vision API
- Python 3.8+ runtime

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file with the following content:
```
# API Configuration
PORT=8000

# Model Selection (local, openai)
MODEL_TYPE=local

# Enable/disable depth estimation for better volume measurement
USE_DEPTH_ESTIMATION=true

# OpenAI Configuration (only needed if MODEL_TYPE=openai)
USE_OPENAI=false
OPENAI_API_KEY=
```

4. If you want to use OpenAI's Vision API, update the `.env` file:
```
MODEL_TYPE=openai
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the API

Start the API server:

```bash
python app.py
```

The API will be available at `http://localhost:8000`.

## How It Works

The API uses three key technologies to provide accurate ingredient recognition and quantity estimation:

1. **Object Detection**: Identifies food items and their boundaries in the image
2. **Object Counting**: Counts discrete items (like apples or eggs) by analyzing bounding boxes
3. **Depth Estimation**: Uses the MiDaS model to estimate the depth/volume of continuous items (like liquids or cheese)

This combination allows for more precise estimates than just using bounding box sizes alone.

## API Endpoints

### `POST /analyze-image`

Upload an image and get ingredients analysis.

**Request**: Multipart form data with an `image` field containing the image file.

**Response**: JSON object with detected ingredients and specific quantities.

Example response:
```json
{
  "ingredients": [
    {
      "name": "apple",
      "confidence": 0.95,
      "estimated_quantity": "3 apples",
      "box_coordinates": [100, 200, 300, 400]
    },
    {
      "name": "milk",
      "confidence": 0.87,
      "estimated_quantity": "1.0 liter",
      "box_coordinates": [50, 100, 150, 300]
    },
    {
      "name": "cheese",
      "confidence": 0.92,
      "estimated_quantity": "250g",
      "box_coordinates": [200, 150, 300, 250]
    }
  ],
  "model_used": "local_huggingface_models",
  "depth_estimation_used": true
}
```

## Notes on Model Selection

- **Local Model**: Uses Hugging Face's pre-trained object detection and classification models combined with MiDaS depth estimation. Faster but less accurate for complex food identification.
- **OpenAI Model**: Uses GPT-4 Vision API. More accurate but requires an API key and internet connection. 