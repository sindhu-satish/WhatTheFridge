# WhatTheFridge - AI Ingredient Detection

An AI-powered app that identifies ingredients in your fridge and estimates their quantities.

## Project Structure

- **UI**: React frontend with drag-and-drop image upload 
- **API**: FastAPI backend powered by OpenAI's Vision API

## Features

- Image upload to analyze fridge contents
- Accurate ingredient detection with specific quantity estimates (e.g., "3 apples", "500ml milk")
- Beautiful, responsive UI with real-time results
- Powered by OpenAI's Vision API for state-of-the-art food recognition

## Technology Stack

- FastAPI for the API framework
- OpenAI's Vision API for food recognition
- Python 3.9+ runtime

## Setup

1. Clone the repository
2. Install backend dependencies:
```bash
pip install -r requirements.txt
```
3. Install frontend dependencies:
```bash
cd UI
npm install
```
4. Create a `.env` file with the following content:
```
# API Configuration
PORT=8000

# OpenAI API Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=1000
```

5. Make sure to add your actual OpenAI API key in the `.env` file.

## Running Locally

### Start the backend:

```bash
python app.py
```

The API will be available at `http://localhost:8000`.

### Start the frontend:

```bash 
cd UI
npm run dev
```

The UI will be available at `http://localhost:5173`.

## Deployment

Due to size limitations with Vercel's serverless functions, we use a split deployment strategy:

1. **Frontend**: Deploy the UI on Vercel
2. **Backend**: Deploy the API on a platform like Render or Railway

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

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
      "estimated_quantity": "3 apples"
    },
    {
      "name": "milk",
      "confidence": 0.87,
      "estimated_quantity": "1 liter"
    },
    {
      "name": "cheese",
      "confidence": 0.92,
      "estimated_quantity": "250g"
    }
  ],
  "model_used": "gpt-4o-mini"
}
```

## Testing the API

You can test the API using cURL:

```bash
curl -X POST -F "image=@/path/to/your/image.jpg" http://localhost:8000/analyze-image
```

Replace `/path/to/your/image.jpg` with the path to an actual image file. 