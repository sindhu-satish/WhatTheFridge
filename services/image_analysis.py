import os
import base64
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import json
import re
import time

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
USE_FAKE_RESPONSE = os.getenv("USE_FAKE_RESPONSE", "false").lower() == "true"

def get_fake_response() -> Dict[str, Any]:
    """
    Generate a fake response for testing purposes when OpenAI API is not available
    """
    return {
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
                "estimated_quantity": "1 liter",
                "box_coordinates": [0, 0, 100, 100]
            },
            {
                "name": "cheese",
                "confidence": 0.82,
                "estimated_quantity": "250g",
                "box_coordinates": [0, 0, 100, 100]
            },
            {
                "name": "yogurt",
                "confidence": 0.78,
                "estimated_quantity": "500g",
                "box_coordinates": [0, 0, 100, 100]
            }
        ],
        "model_used": "fake_response_for_testing"
    }

def analyze_image_with_openai(image_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze an image using OpenAI's Vision API to identify ingredients and their quantities
    
    Args:
        image_bytes: Raw bytes of the uploaded image
        
    Returns:
        Dictionary with detected ingredients and their quantities
    """
    # Return fake response if requested (for testing without API access)
    if USE_FAKE_RESPONSE:
        print("Using fake response for testing (USE_FAKE_RESPONSE=true)")
        return get_fake_response()
    
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
        print("OpenAI API key is not properly set")
        return {
            "error": "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.",
            "ingredients": [],
            "model_used": "error"
        }
    
    # Convert image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Simplified API call using the vision endpoint
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Identify food items in this image. Return a JSON with array 'ingredients' containing objects with 'name', 'estimated_quantity', and 'confidence' fields."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": MAX_TOKENS
    }
    
    try:
        # Simple POST request with minimal retries
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            try:
                # Extract the content from the response
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse JSON from the content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_json = json.loads(json_str)
                    parsed_json["model_used"] = OPENAI_MODEL
                    return parsed_json
                else:
                    try:
                        parsed_json = json.loads(content)
                        parsed_json["model_used"] = OPENAI_MODEL
                        return parsed_json
                    except:
                        pass
            except:
                pass
            
            # If all parsing attempts fail, return a fallback response
            return {
                "ingredients": [],
                "error": "Failed to parse OpenAI response",
                "model_used": OPENAI_MODEL
            }
        else:
            # Handle error response
            return {
                "ingredients": [],
                "error": f"OpenAI API error: {response.status_code}",
                "model_used": "error"
            }
    
    except Exception as e:
        # Handle request errors
        return {
            "ingredients": [],
            "error": f"Request error: {str(e)}",
            "model_used": "error"
        }

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Main function to analyze an image of food/fridge contents
    
    Args:
        image_bytes: Raw bytes of the uploaded image
        
    Returns:
        Dictionary with detected ingredients and quantities
    """
    # Return fake response in development to avoid API costs
    if os.environ.get("VERCEL_ENV") != "production":
        print("Using fake response in development environment")
        return get_fake_response()
        
    return analyze_image_with_openai(image_bytes) 