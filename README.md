# WhatTheFridge - AI Ingredient Detection API

This backend API uses OpenAI's Vision API to identify ingredients in fridge images and estimate their quantities.

## Features

- Image upload endpoint to analyze fridge contents
- Accurate ingredient detection with specific quantity estimates (e.g., "3 apples", "500ml milk")
- Powered by OpenAI's GPT-4 Vision API for state-of-the-art food recognition

## Technology Stack

- FastAPI for the API framework
- OpenAI's GPT-4 Vision API for food recognition
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

# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-vision-preview
MAX_TOKENS=1000
```

4. Make sure to add your actual OpenAI API key in the `.env` file.

## Running the API

Start the API server:

```bash
python app.py
```

The API will be available at `http://localhost:8000`.

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
      "box_coordinates": [0, 0, 100, 100]
    },
    {
      "name": "milk",
      "confidence": 0.87,
      "estimated_quantity": "1.0 liter",
      "box_coordinates": [0, 0, 100, 100]
    },
    {
      "name": "cheese",
      "confidence": 0.92,
      "estimated_quantity": "250g",
      "box_coordinates": [0, 0, 100, 100]
    }
  ],
  "model_used": "gpt-4-vision-preview"
}
```

## Testing with cURL

You can test the API using cURL:

```bash
curl -X POST -F "image=@/path/to/your/image.jpg" http://localhost:8000/analyze-image
```

Replace `/path/to/your/image.jpg` with the path to an actual image file. 