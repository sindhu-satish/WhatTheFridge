export interface Ingredient {
  name: string;
  estimated_quantity: string;
  confidence: number;
}

export interface Recipe {
  title: string;
  ingredients: string[];
  instructions: string[];
  prepTime: string;
  cookTime: string;
}

export interface AnalysisResponse {
  ingredients: Ingredient[];
  recipes?: Recipe[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'http://0.0.0.0:8000/api';

export async function analyzeImage(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch(`${API_BASE_URL}/analyze-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error analyzing image:', error);
    throw error;
  }
}

export async function getRecipes(ingredients: Ingredient[]): Promise<{ recipes: Recipe[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/get-recipes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ingredients }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    console.log('Raw response:', await response.text());  // Log raw response for debugging
    
    // Create a new response with the logged body
    const clonedResponse = new Response(response.body);
    const data = await clonedResponse.json();
    console.log('Parsed response:', data);  // Log parsed response
    return data;
  } catch (error) {
    console.error('Error getting recipes:', error);
    throw error;
  }
} 