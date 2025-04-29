'use client';

import React from 'react';

interface Recipe {
  title: string;
  ingredients: string[];
  instructions: string[];
  prepTime: string;
  cookTime: string;
}

interface RecipesListProps {
  recipes: Recipe[];
}

export function RecipesList({ recipes }: RecipesListProps) {
  return (
    <div className="space-y-8">
      {recipes.map((recipe, index) => (
        <div key={index} className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-bold text-gray-900 mb-4">{recipe.title}</h3>
          
          <div className="flex space-x-4 text-sm text-gray-500 mb-4">
            <div>
              <span className="font-medium">Prep time:</span> {recipe.prepTime}
            </div>
            <div>
              <span className="font-medium">Cook time:</span> {recipe.cookTime}
            </div>
          </div>
          
          <div className="mb-4">
            <h4 className="font-medium text-gray-900 mb-2">Ingredients:</h4>
            <ul className="list-disc list-inside space-y-1 text-gray-600">
              {recipe.ingredients.map((ingredient, i) => (
                <li key={i}>{ingredient}</li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Instructions:</h4>
            <ol className="list-decimal list-inside space-y-2 text-gray-600">
              {recipe.instructions.map((step, i) => (
                <li key={i} className="leading-relaxed">{step}</li>
              ))}
            </ol>
          </div>
        </div>
      ))}
    </div>
  );
} 