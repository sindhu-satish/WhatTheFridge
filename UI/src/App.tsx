import React, { useEffect, useState, useRef } from 'react';
import { UploadIcon, SendIcon, ImageIcon, Loader2Icon } from 'lucide-react';
import { analyzeImage, type AnalysisResponse, type Ingredient } from './services/api';

type MessageContent = string | AnalysisResponse;

interface Message {
  type: 'user' | 'system';
  content: MessageContent;
}

export function App() {
  const [messages, setMessages] = useState<Message[]>([{
    type: 'system',
    content: "Welcome to WhatTheFridge! Upload an image of your fridge or food items, and I'll identify the ingredients for you."
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
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
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'system',
        content: `Error analyzing image: ${error instanceof Error ? error.message : 'Unknown error'}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  const startNewScan = () => {
    setMessages([{
      type: 'system',
      content: 'Ready for a new scan! Upload another image of your fridge or food items.'
    }]);
  };
  
  const renderMessageContent = (message: Message) => {
    if (typeof message.content === 'string') {
      if (message.content.startsWith('data:image')) {
        return <div className="max-w-sm overflow-hidden rounded-lg">
            <img src={message.content} alt="Uploaded food" className="w-full h-auto object-cover" />
          </div>;
      }
      return <p className="text-sm">{message.content}</p>;
    } else if (message.content.ingredients) {
      return <IngredientsTable ingredients={message.content.ingredients} />;
    }
    return null;
  };
  
  return <div className="flex flex-col w-full h-screen bg-gray-50">
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
          {messages.map((message, index) => <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`rounded-xl p-4 max-w-[80%] shadow-sm
                  ${message.type === 'user' ? 'bg-blue-500 text-white rounded-br-none' : 'bg-white text-gray-800 rounded-bl-none'}`}>
                {renderMessageContent(message)}
              </div>
            </div>)}
          {isLoading && <div className="flex justify-start">
              <div className="rounded-xl p-4 bg-white text-gray-800 rounded-bl-none shadow-sm flex items-center space-x-2">
                <Loader2Icon className="h-5 w-5 animate-spin text-blue-500" />
                <p className="text-sm">Analyzing your image...</p>
              </div>
            </div>}
          <div ref={messagesEndRef} />
        </div>
        <div className="relative">
          <div className={`border-2 rounded-xl p-8 text-center transition-all duration-300 ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-dashed border-gray-300'}`} onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}>
            <input ref={fileInputRef} type="file" onChange={handleFileChange} className="hidden" accept="image/*" />
            <div className="flex flex-col items-center justify-center">
              <UploadIcon className="h-10 w-10 text-blue-500 mb-2" />
              <p className="text-sm text-gray-600 mb-2">
                Drag and drop an image here, or click to select
              </p>
              <button onClick={handleUploadClick} className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center">
                <ImageIcon className="h-4 w-4 mr-2" />
                Upload Image
              </button>
            </div>
          </div>
          {messages.length > 1 && <button onClick={startNewScan} className="mt-3 text-blue-500 text-sm hover:underline">
              Start a new scan
            </button>}
        </div>
      </main>
    </div>;
}

interface IngredientsTableProps {
  ingredients: Ingredient[];
}

function IngredientsTable({ ingredients }: IngredientsTableProps) {
  return <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-100">
            <th className="text-left py-2 px-3 font-medium">Ingredient</th>
            <th className="text-left py-2 px-3 font-medium">Quantity</th>
            <th className="text-left py-2 px-3 font-medium">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {ingredients.sort((a, b) => b.confidence - a.confidence).map((ingredient, index) => <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="py-2 px-3">{ingredient.name}</td>
              <td className="py-2 px-3">{ingredient.estimated_quantity}</td>
              <td className="py-2 px-3">
                <div className="flex items-center">
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mr-2">
                    <div className="bg-blue-500 h-1.5 rounded-full" style={{
                  width: `${ingredient.confidence * 100}%`
                }}></div>
                  </div>
                  <span>{Math.round(ingredient.confidence * 100)}%</span>
                </div>
              </td>
            </tr>)}
        </tbody>
      </table>
    </div>;
}