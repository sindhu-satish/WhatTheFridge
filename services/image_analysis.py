import os
import base64
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import json
import re
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
USE_FAKE_RESPONSE = os.getenv("USE_FAKE_RESPONSE", "false").lower() == "true"

def get_fake_response() -> Dict[str, Any]:
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

def extract_json_from_markdown(content: str) -> Dict[str, Any]:
    """
    Extract JSON from markdown code blocks.
    Args:
        content: String containing markdown with JSON code block
    Returns:
        Parsed JSON object
    """
    content = content.strip()
    if content.startswith('```json'):
        content = content[7:]  
    if content.startswith('```'):
        content = content[3:]  
    if content.endswith('```'):
        content = content[:-3] 
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from markdown: {e}")
        return {"ingredients": [], "error": "Failed to parse JSON response"}

def analyze_image_with_openai(image_bytes: bytes) -> Dict[str, Any]:
    logger.debug("Starting image analysis")
    
    if USE_FAKE_RESPONSE:
        print("Using fake response for testing (USE_FAKE_RESPONSE=true)")
        return get_fake_response()
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is not set")
        return {
            "ingredients": [],
            "model_used": "error",
            "error": "OpenAI API key is not set"
        }
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    logger.debug("Image converted to base64")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''Analyze this image of food items. For each food item you detect, provide:
                        1. The name of the food item
                        2. An estimated quantity (e.g., '2 apples', '1 liter of milk')
                        3. Your confidence level in the detection (0-1)
                        Format the response as a JSON object with an 'ingredients' array. 
                        Each ingredient should have 'name', 'estimated_quantity', and 'confidence' fields.
                        Follow these rules:
                        If the item detected looks like     
                            {
                                "name": "Bell peppers",
                                "estimated_quantity": "2 bell peppers (1 yellow, 1 red)",
                                "confidence": 0.9
                            },
                        then the each item should be a separate ingredient, like this:
                        ```json
                        {
                            "name": "Red bell peppers",
                            "estimated_quantity": "1",
                            "confidence": 0.9
                        },
                        {
                            "name": "Yellow bell peppers",
                            "estimated_quantity": "1",
                            "confidence": 0.9
                        }
                        ```

                        If the item detected looks like Condiment bottles (e.g., ketchup, 
                        salad dressing), then each item should be a separate ingredient, like this:
                        ```json
                        {
                            "name": "Ketchup",
                            "estimated_quantity": "1",
                            "confidence": 0.9
                        },
                        {
                            "name": "Salad dressing",
                            "estimated_quantity": "1",
                            "confidence": 0.9
                        }
                        ```
                        '''
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
    
    logger.debug(f"Using OpenAI model: {OPENAI_MODEL}")
    
    try:
        logger.debug("Making request to OpenAI API")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.debug(f"OpenAI API response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.debug("Successfully received JSON response from OpenAI")
            content = result["choices"][0]["message"]["content"]
            logger.debug(f"OpenAI response content: {content}")
            
            parsed_response = extract_json_from_markdown(content)
            parsed_response["model_used"] = OPENAI_MODEL
            logger.debug("Successfully parsed response JSON")
            return parsed_response
        else:
            error_msg = f"OpenAI API error: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            return {
                "ingredients": [],
                "model_used": "error",
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Exception during API call: {str(e)}")
        return {
            "ingredients": [],
            "model_used": "error",
            "error": str(e)
        }

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    if os.environ.get("VERCEL_ENV") != "production":
        print("Using fake response in development environment")
        return get_fake_response()
        
    return analyze_image_with_openai(image_bytes) 