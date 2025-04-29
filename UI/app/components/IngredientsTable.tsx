'use client';

import React from 'react';
import type { Ingredient } from '../services/api';

interface SelectedIngredient extends Ingredient {
  selected: boolean;
}

interface IngredientsTableProps {
  ingredients: Ingredient[];
  selectedIngredients: SelectedIngredient[];
  onIngredientSelect: (ingredient: Ingredient) => void;
}

export function IngredientsTable({ ingredients, selectedIngredients, onIngredientSelect }: IngredientsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Ingredient
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Estimated Quantity
            </th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Confidence
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {ingredients.map((ingredient, index) => {
            const isSelected = selectedIngredients.some(i => i.name === ingredient.name);
            return (
              <tr 
                key={index}
                onClick={() => onIngredientSelect(ingredient)}
                className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {ingredient.name}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {ingredient.estimated_quantity}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {Math.round(ingredient.confidence * 100)}%
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
} 