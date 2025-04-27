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
    
    # Explicitly instruct the model to return JSON
    prompt = (
        "You are an expert food recognition system. Analyze this image of food items or a fridge interior. "
        "Identify all food ingredients visible in the image. For each ingredient, provide: "
        "1) the name of the ingredient (be specific), "
        "2) an estimated specific quantity (e.g., '3 apples', '500ml milk', '250g cheese'), and "
        "3) a confidence score from 0 to 1 representing how certain you are about this item. "
        "\n\nYou MUST respond with a valid JSON object with an array called 'ingredients' where each item has "
        "fields 'name', 'estimated_quantity', and 'confidence'. Be precise with the quantities - use counts "
        "for discrete items, volume (ml, liters) for liquids, and weight (g, kg) for solid foods."
        "\n\nIf the image is not clear or doesn't contain food, include an 'error' field in your JSON response."
        "\n\nYOUR ENTIRE RESPONSE MUST BE VALID JSON WITHOUT ANY ADDITIONAL TEXT."
    )
    
    # Use the new responses API format
    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text", 
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ]
    }
    
    try:
        # Print debugging info
        print(f"Calling OpenAI API with model: {OPENAI_MODEL}")
        print(f"API URL: https://api.openai.com/v1/responses")
        print(f"API key length: {len(OPENAI_API_KEY)} characters")
        
        # Add a retry mechanism
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/responses", 
                    headers=headers, 
                    json=payload,
                    timeout=30  # Add timeout
                )
                
                # Print response for debugging
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.text[:300]}...")  # Print first 300 chars
                
                # Check for rate limiting
                if response.status_code == 429:
                    print(f"Rate limited. Attempt {attempt+1}/{max_retries}. Waiting {retry_delay} seconds.")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                    
                # Break on other status codes
                break
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"Connection error on attempt {attempt+1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
        
        # Process response
        if response.status_code == 200:
            response_data = response.json()
            
            # Debug the response structure
            print(f"Response data keys: {response_data.keys()}")
            
            # Check if the response has the expected structure
            if "content" in response_data and isinstance(response_data["content"], list) and len(response_data["content"]) > 0:
                response_text = response_data["content"][0].get("text", "")
                print(f"Extracted text: {response_text[:100]}...")  # Print first 100 chars
            else:
                # Fall back to the raw response if the structure is unexpected
                print("Unexpected response structure, using raw response")
                response_text = json.dumps(response_data)
            
            # Try to extract JSON using regex (in case the model outputs additional text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    print(f"Extracted JSON: {json_str[:100]}...")  # Print first 100 chars
                    result = json.loads(json_str)
                    result["model_used"] = OPENAI_MODEL
                    
                    # Add default coordinates for visualization purposes
                    for item in result.get("ingredients", []):
                        if "box_coordinates" not in item:
                            item["box_coordinates"] = [0, 0, 100, 100]  # Dummy coordinates
                    
                    return result
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from regex match: {str(e)}")
            
            # If JSON extraction failed, try parsing the whole response
            try:
                result = json.loads(response_text)
                result["model_used"] = OPENAI_MODEL
                return result
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from whole response: {str(e)}")
                
                # Fall back to the fake response but include details about the error
                fake_response = get_fake_response()
                fake_response["error"] = "Failed to parse OpenAI response as JSON"
                fake_response["raw_response"] = response_text[:500]  # Include part of the raw response
                return fake_response
        else:
            # Handle error response
            error_message = f"OpenAI API returned status code {response.status_code}"
            try:
                error_data = response.json()
                print(f"Error data: {error_data}")
                error_detail = error_data.get("error", {}).get("message", "Unknown error")
                error_message = f"{error_message}: {error_detail}"
            except:
                error_message = f"{error_message}: {response.text}"
            
            print(f"API Error: {error_message}")
            
            # Return fake response for testing to avoid blocking development
            print("Returning fake test response due to API error")
            fake_response = get_fake_response()
            fake_response["error"] = error_message
            return fake_response
    
    except Exception as e:
        # Handle request errors (network issues, API errors, etc.)
        error_msg = f"Error making API request: {str(e)}"
        print(f"Exception: {error_msg}")
        
        # Return fake response for testing
        print("Returning fake test response due to exception")
        fake_response = get_fake_response()
        fake_response["error"] = error_msg
        return fake_response

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Main function to analyze an image of food/fridge contents
    
    Args:
        image_bytes: Raw bytes of the uploaded image
        
    Returns:
        Dictionary with detected ingredients and quantities
    """
    return analyze_image_with_openai(image_bytes) 