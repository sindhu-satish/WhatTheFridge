// API service for WhatTheFridge

// Use an external API URL in production, and local development server for testing
const BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://whatthefridge-api.onrender.com' // Replace with your actual deployed backend URL
  : 'http://localhost:8000';

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
    // For testing in production without a backend
    if (process.env.NODE_ENV === 'production' && !BASE_URL.startsWith('http')) {
      // Return fake data for demo purposes until the backend is deployed
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API delay
      return {
        ingredients: [
          { name: 'Apple', estimated_quantity: '3 apples', confidence: 0.95 },
          { name: 'Milk', estimated_quantity: '1 liter', confidence: 0.87 },
          { name: 'Cheese', estimated_quantity: '250g', confidence: 0.82 },
          { name: 'Yogurt', estimated_quantity: '500g', confidence: 0.78 },
          { name: 'Lettuce', estimated_quantity: '1 head', confidence: 0.75 },
          { name: 'Tomato', estimated_quantity: '4 tomatoes', confidence: 0.72 },
          { name: 'Cucumber', estimated_quantity: '2 cucumbers', confidence: 0.68 },
          { name: 'Orange', estimated_quantity: '2 oranges', confidence: 0.65 }
        ],
        model_used: 'demo_mode'
      };
    }

    const response = await fetch(`${BASE_URL}/analyze-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error (${response.status}): ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error analyzing image:', error);
    throw error;
  }
} 