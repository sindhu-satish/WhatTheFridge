# WhatTheFridge - AI Ingredient Detection

An AI-powered app that identifies ingredients in your fridge and estimates their quantities, then suggests recipes based on the available ingredients.

## Features

- Image upload to analyze fridge contents
- Accurate ingredient detection with specific quantity estimates (e.g., "3 apples", "500ml milk")
- Recipe recommendations based on detected ingredients
- Beautiful, responsive UI with real-time results
- Powered by OpenAI's Vision API for state-of-the-art food recognition

## Technology Stack

### Backend
- FastAPI for the API framework
- OpenAI's Vision API for food recognition
- Python 3.9+ runtime

### Frontend
- Vite
- React
- Tailwind CSS
- TypeScript

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.9 or higher
- Node.js 18 or higher
- npm 
- Git

## Setup

### Quick Setup (Recommended)

The easiest way to set up the project is by using the provided build script:

```bash
# Clone the repository
git clone https://github.com/sindhu-satish/WhatTheFridge.git
cd WhatTheFridge

# Make the build script executable
chmod +x build.sh

# Run the build script
./build.sh
```

The build script will:
- Create and activate a Python virtual environment
- Install backend dependencies
- Set up the .env file (you'll need to add your OpenAI API key)
- Install frontend dependencies

### Manual Setup

If you prefer to set up manually, follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/sindhu-satish/WhatTheFridge.git
cd WhatTheFridge
```

2. Set up the backend:
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Create a .env file in the root directory with your OpenAI API key:
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
echo "USE_FAKE_RESPONSE=false > .env"
echo "PORT=8000 > .env"
echo "OPENAI_MODEL=gpt-4.1" >> .env
echo "MAX_TOKENS=1000" >> .env
```

3. Set up the frontend:
```bash
# Navigate to the UI directory
cd UI

# Install frontend dependencies
npm install
```

## Running the Application

You'll need to run both the backend and frontend services:

### Start the Backend Server

In the root directory with your virtual environment activated:
```bash
# From the root directory
python app.py
```
The backend API will be available at `http://localhost:8000/api`.

### Start the Frontend Development Server

In a new terminal:
```bash
# Navigate to the UI directory
cd UI

# Start the development server
npm run dev
```
The frontend will be available at `http://localhost:8000`.

## Using the Application

1. Open `http://localhost:8000` in your browser
2. Upload an image of your fridge or food items using the upload button or drag-and-drop
3. Wait for the AI to analyze the image and detect ingredients
4. Select ingredients from the detected list
5. Click "Get Recipe Recommendations" to receive recipe suggestions based on your selected ingredients

## API Endpoints

### `POST /api/analyze-image`
Analyzes an uploaded image and returns detected ingredients.

**Request**: Multipart form data with an `image` field containing the image file.

**Response**: JSON object with detected ingredients and confidence scores.

### `POST /api/get-recipes`
Gets recipe recommendations based on selected ingredients.

**Request**: JSON object with an array of ingredients.

**Response**: JSON object with recommended recipes.

## Error Handling

The application includes handling for:
- Invalid image formats
- Failed image uploads
- API timeouts
- No ingredients detected
- Recipe recommendation failures

## Development

To run the application in development mode with hot reloading:

1. Backend:
```bash
# From the root directory
uvicorn app:app --reload
```

2. Frontend:
```bash
# From the UI directory
npm run dev
```