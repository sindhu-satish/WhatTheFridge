const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // In production, use relative path
  : 'http://0.0.0.0:8000/api';  // In development, use full URL

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

export async function analyzeImage(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch(`${API_BASE_URL}/analyze-image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function getRecipes(ingredients: Ingredient[]): Promise<RecipeResponse> {
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

  return response.json();
} 