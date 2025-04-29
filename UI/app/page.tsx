'use client';

import React, { useEffect, useState, useRef } from 'react';
import Image from 'next/image';
import { UploadIcon, SendIcon, ImageIcon, Loader2Icon, ChefHatIcon } from 'lucide-react';
import { analyzeImage, type AnalysisResponse, type Ingredient, getRecipes } from './services/api';
import { IngredientsTable } from './components/IngredientsTable';
import { RecipesList } from './components/RecipesList';

type MessageContent = string | AnalysisResponse;

interface Message {
  type: 'user' | 'system';
  content: MessageContent;
}

interface ExtendedAnalysisResponse extends AnalysisResponse {
  recipes?: Recipe[];
}

interface Recipe {
  title: string;
  ingredients: string[];
  instructions: string[];
  prepTime: string;
  cookTime: string;
}

interface SelectedIngredient extends Ingredient {
  selected: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([{
    type: 'system',
    content: "Welcome to WhatTheFridge! Upload an image of your fridge or food items, and I'll identify the ingredients for you."
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingRecipes, setIsFetchingRecipes] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedIngredients, setSelectedIngredients] = useState<SelectedIngredient[]>([]);
  const [_recipes, setRecipes] = useState<Recipe[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages]);
  
  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };
  
  const handleFile = (file: File) => {
    if (!file.type.match('image.*')) {
      setMessages(prev => [...prev, {
        type: 'system',
        content: 'Please upload an image file.'
      }]);
      return;
    }
    
    const reader = new FileReader();
    reader.onloadend = () => {
      setMessages(prev => [...prev, {
        type: 'user',
        content: reader.result as string
      }]);
      processImage(file);
    };
    reader.readAsDataURL(file);
  };
  
  const processImage = async (file: File) => {
    setIsLoading(true);
    
    try {
      const response = await analyzeImage(file);
      setMessages(prev => [...prev, {
        type: 'system',
        content: response
      }]);
      
      if (response.ingredients && response.ingredients.length === 0) {
        setMessages(prev => [...prev, {
          type: 'system',
          content: "No ingredients were detected in the image. Please try uploading a clearer image or try again."
        }]);
      } else {
        setMessages(prev => [...prev, {
          type: 'system',
          content: 'Please select ingredients from above to get recipe recommendations. Or you can try another image.'
        }]);
      }
    } catch (error) {
      const errorMessage = error instanceof Error && error.message.includes('timeout') 
        ? "I was unable to reach OpenAI's servers. Please try again."
        : `Error analyzing image: ${error instanceof Error ? error.message : 'Unknown error'}`;
      
      setMessages(prev => [...prev, {
        type: 'system',
        content: errorMessage
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // Reset the input to allow selecting the same file again
      fileInputRef.current.click();
    }
  };
  
  const handleIngredientSelect = (ingredient: Ingredient) => {
    setSelectedIngredients(prev => {
      const existing = prev.find(i => i.name === ingredient.name);
      if (existing) {
        return prev.filter(i => i.name !== ingredient.name);
      } else {
        return [...prev, { ...ingredient, selected: true }];
      }
    });
  };

  const handleGetRecipes = async () => {
    if (selectedIngredients.length === 0) {
      setMessages(prev => [...prev, {
        type: 'system',
        content: 'Please select at least one ingredient to get recipe recommendations.'
      }]);
      return;
    }

    setIsFetchingRecipes(true);
    try {
      const recipeResponse = await getRecipes(selectedIngredients);
      setRecipes(recipeResponse.recipes);
      setMessages(prev => [...prev, {
        type: 'system',
        content: {
          ingredients: [],
          recipes: recipeResponse.recipes
        } as ExtendedAnalysisResponse
      }]);
    } catch (error) {
      const errorMessage = error instanceof Error && error.message.includes('timeout')
        ? "I was unable to reach OpenAI's servers. Please try again."
        : `Error getting recipes: ${error instanceof Error ? error.message : 'Unknown error'}`;

      setMessages(prev => [...prev, {
        type: 'system',
        content: errorMessage
      }]);
    } finally {
      setIsFetchingRecipes(false);
    }
  };
  
  const renderMessageContent = (message: Message) => {
    if (!message.content) {
      return null;
    }

    if (typeof message.content === 'string') {
      if (message.content.startsWith('data:image')) {
        return (
          <div className="max-w-sm overflow-hidden rounded-lg relative h-64">
            <Image 
              src={message.content}
              alt="Uploaded food"
              fill
              style={{ objectFit: 'cover' }}
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
          </div>
        );
      }
      if (!message.content.trim()) {
        return null;
      }
      return <p className="text-sm">{message.content}</p>;
    } else if (message.content.ingredients && message.content.ingredients.length > 0) {
      return <div>
        <IngredientsTable 
          ingredients={message.content.ingredients} 
          selectedIngredients={selectedIngredients}
          onIngredientSelect={handleIngredientSelect}
        />
        {selectedIngredients.length > 0 && (
          <button 
            onClick={handleGetRecipes}
            disabled={isFetchingRecipes}
            className="mt-4 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors flex items-center disabled:opacity-50"
          >
            <ChefHatIcon className="h-4 w-4 mr-2" />
            {isFetchingRecipes ? 'Fetching Recipes...' : 'Get Recipe Recommendations'}
          </button>
        )}
      </div>;
    } else if (message.content.recipes && message.content.recipes.length > 0) {
      return <RecipesList recipes={message.content.recipes} />;
    }
    return null;
  };
  
  return (
    <div className="flex flex-col w-full h-screen bg-gray-50">
      <header className="bg-blue-500 text-white px-4 py-4 shadow-md">
        <div className="max-w-4xl mx-auto flex items-center">
          <div className="bg-white p-2 rounded-full mr-3">
            <ImageIcon className="h-6 w-6 text-blue-500" />
          </div>
          <h1 className="text-xl font-bold">WhatTheFridge</h1>
        </div>
      </header>
      <main className="flex-1 overflow-hidden flex flex-col max-w-4xl w-full mx-auto p-4">
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          {messages.map((message, index) => {
            const content = renderMessageContent(message);
            if (!content) {
              return null;
            }
            return (
              <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`rounded-xl p-4 max-w-[80%] shadow-sm
                    ${message.type === 'user' ? 'bg-blue-500 text-white rounded-br-none' : 'bg-white text-gray-800 rounded-bl-none'}`}>
                  {content}
                </div>
              </div>
            );
          })}
          {isLoading && <div className="flex justify-start">
              <div className="rounded-xl p-4 bg-white text-gray-800 rounded-bl-none shadow-sm flex items-center space-x-2">
                <Loader2Icon className="h-5 w-5 animate-spin text-blue-500" />
                <p className="text-sm">Analyzing your image...</p>
              </div>
            </div>}
          {isFetchingRecipes && <div className="flex justify-start">
              <div className="rounded-xl p-4 bg-white text-gray-800 rounded-bl-none shadow-sm flex items-center space-x-2">
                <Loader2Icon className="h-5 w-5 animate-spin text-green-500" />
                <p className="text-sm">Fetching recipes for the selected ingredients...</p>
              </div>
            </div>}
          <div ref={messagesEndRef} />
        </div>
        <div className="relative">
          <div 
            className={`border-2 rounded-xl p-8 text-center transition-all duration-300 ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-dashed border-gray-300'
            }`} 
            onDragEnter={handleDrag} 
            onDragOver={handleDrag} 
            onDragLeave={handleDrag} 
            onDrop={handleDrop}
          >
            <input 
              ref={fileInputRef} 
              type="file" 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*" 
            />
            <div className="flex flex-col items-center justify-center">
              <UploadIcon className="h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-600 mb-2">Drag and drop your image here, or</p>
              <button
                onClick={handleUploadClick}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center"
              >
                <SendIcon className="h-4 w-4 mr-2" />
                Upload Image
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 