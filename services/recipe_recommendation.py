import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

def get_recipe_recommendations(ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get recipe recommendations based on selected ingredients using OpenAI.
    
    Args:
        ingredients: List of selected ingredients with their quantities
        
    Returns:
        Dictionary containing recommended recipes
    """
    logger.debug(f"Received ingredients: {ingredients}")
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is not set")
        return {
            "recipes": [],
            "error": "OpenAI API key is not set"
        }
    
    if not ingredients:
        logger.error("No ingredients provided")
        return {
            "recipes": [],
            "error": "No ingredients provided"
        }
    
    try:
        # Format ingredients for the prompt
        ingredients_list = [f"{ing['name']} ({ing['estimated_quantity']})" for ing in ingredients]
        ingredients_text = ", ".join(ingredients_list)
        logger.debug(f"Formatted ingredients: {ingredients_text}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        prompt = f"""Based on these ingredients: {ingredients_text}
        Please suggest 3 recipes that can be made using these ingredients. 
        For each recipe, provide:
        1. A creative title
        2. List of all ingredients needed (including quantities)
        3. Step-by-step cooking instructions
        4. Estimated preparation time
        5. Estimated cooking time
        
        IMPORTANT: Respond ONLY with a JSON object. Do not include any additional text, explanations, or notes.
        Your entire response must be valid JSON wrapped in ```json ``` markers.
        
        Format the response as a JSON object with a 'recipes' array. Each recipe should have:
        - title (string)
        - ingredients (array of strings)
        - instructions (array of strings)
        - prepTime (string)
        - cookTime (string)
        
        Example format:
        ```json
        {{
          "recipes": [
            {{
              "title": "Recipe Title",
              "ingredients": ["1 cup ingredient1", "2 tbsp ingredient2"],
              "instructions": ["Step 1", "Step 2"],
              "prepTime": "10 minutes",
              "cookTime": "20 minutes"
            }}
          ]
        }}
        ```
        """
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "response_format": { "type": "json_object" }
        }
        
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
            content = result["choices"][0]["message"]["content"]
            logger.debug(f"OpenAI response content: {content}")
            
            try:
                # Extract JSON content between ```json ``` markers if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                
                # Extract JSON from the response
                recipes_data = json.loads(content)
                logger.debug(f"Parsed recipes data: {recipes_data}")
                return recipes_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse recipe response: {e}")
                logger.error(f"Raw response content: {content}")
                return {
                    "recipes": [],
                    "error": f"Failed to parse recipe response: {str(e)}"
                }
        else:
            error_msg = f"OpenAI API error: {response.status_code}"
            if response.text:
                error_msg += f" - {response.text}"
            logger.error(error_msg)
            return {
                "recipes": [],
                "error": error_msg
            }
            
    except Exception as e:
        logger.error(f"Exception during recipe API call: {str(e)}")
        return {
            "recipes": [],
            "error": str(e)
        } 