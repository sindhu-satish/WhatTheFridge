
const BASE_URL = 'http://0.0.0.0:8000';

export interface Ingredient {
  name: string;
  estimated_quantity: string;
  confidence: number;
  box_coordinates?: number[];
}

export interface AnalysisResponse {
  ingredients: Ingredient[];
  model_used?: string;
  error?: string;
}

/**
 * Analyze an image of food/fridge contents
 * 
 * @param imageFile - The image file to analyze
 * @returns Promise with analysis results
 */
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