const BASE_URL = 'http://0.0.0.0:8000/api';

export interface Ingredient {
  name: string;
  estimated_quantity: string;
  confidence: number;
  box_coordinates?: number[];
}

export interface AnalysisResponse {
  ingredients: Ingredient[];
  model_name?: string;
  error?: string;
}

export interface Recipe {
  title: string;
  ingredients: string[];
  instructions: string[];
  prepTime: string;
  cookTime: string;
}

export interface RecipeResponse {
  recipes: Recipe[];
  error?: string;
}

export async function analyzeImage(imageFile: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('image', imageFile);

  try {
    const response = await fetch(`${BASE_URL}/analyze-image`, {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to analyze image');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to analyze image');
  }
}

export async function getRecipes(ingredients: Ingredient[]): Promise<RecipeResponse> {
  const response = await fetch(`${BASE_URL}/get-recipes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ingredients }),
  });

  if (!response.ok) {
    throw new Error('Failed to get recipes');
  }

  return response.json();
} 