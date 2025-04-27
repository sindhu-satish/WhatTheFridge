import io
import os
import base64
import requests
from PIL import Image
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import torch
import cv2
from transformers import AutoFeatureExtractor, AutoModelForObjectDetection, AutoProcessor, AutoModelForImageClassification
from dotenv import load_dotenv
import math
from collections import defaultdict
from services.depth_estimation import depth_estimator

load_dotenv()
USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_TYPE = os.getenv("MODEL_TYPE", "local")  
USE_DEPTH_ESTIMATION = os.getenv("USE_DEPTH_ESTIMATION", "true").lower() == "true"

_models = {}

REFERENCE_SIZES = {
    "apple": {"area": 30000, "unit": "whole", "avg_weight": 150, "density": 0.8, "countable": True},  
    "banana": {"area": 40000, "unit": "whole", "avg_weight": 120, "density": 0.9, "countable": True},
    "orange": {"area": 28000, "unit": "whole", "avg_weight": 130, "density": 0.9, "countable": True},
    "carrot": {"area": 20000, "unit": "whole", "avg_weight": 60, "density": 0.6, "countable": True},
    "broccoli": {"area": 50000, "unit": "whole", "avg_weight": 225, "density": 0.4, "countable": True},
    "bottle": {"area": 70000, "unit": "ml", "avg_volume": 500, "density": 1.0, "countable": True},
    "milk": {"area": 70000, "unit": "ml", "avg_volume": 1000, "density": 1.0, "countable": False},
    "pizza": {"area": 150000, "unit": "slice", "avg_weight": 100, "density": 0.3, "countable": True},
    "sandwich": {"area": 60000, "unit": "whole", "avg_weight": 200, "density": 0.4, "countable": True},
    "cake": {"area": 80000, "unit": "slice", "avg_weight": 120, "density": 0.7, "countable": True},
    "donut": {"area": 25000, "unit": "whole", "avg_weight": 60, "density": 0.5, "countable": True},
    "cheese": {"area": 40000, "unit": "g", "avg_weight": 250, "density": 1.1, "countable": False},
    "butter": {"area": 20000, "unit": "g", "avg_weight": 250, "density": 0.95, "countable": False},
    "yogurt": {"area": 35000, "unit": "g", "avg_weight": 150, "density": 1.05, "countable": False},
    "rice": {"area": 30000, "unit": "g", "avg_weight": 200, "density": 0.8, "countable": False},
    "pasta": {"area": 40000, "unit": "g", "avg_weight": 250, "density": 0.4, "countable": False},
    "bread": {"area": 60000, "unit": "slice", "avg_weight": 30, "density": 0.2, "countable": True},
    "egg": {"area": 15000, "unit": "whole", "avg_weight": 60, "density": 1.1, "countable": True},
    "tomato": {"area": 25000, "unit": "whole", "avg_weight": 150, "density": 0.95, "countable": True},
    "cucumber": {"area": 35000, "unit": "whole", "avg_weight": 300, "density": 0.6, "countable": True},
    "lettuce": {"area": 45000, "unit": "g", "avg_weight": 300, "density": 0.1, "countable": False},
    "onion": {"area": 20000, "unit": "whole", "avg_weight": 150, "density": 0.9, "countable": True},
    "potato": {"area": 30000, "unit": "whole", "avg_weight": 200, "density": 0.8, "countable": True},
    "meat": {"area": 50000, "unit": "g", "avg_weight": 300, "density": 1.0, "countable": False},
    "fish": {"area": 60000, "unit": "g", "avg_weight": 250, "density": 0.8, "countable": False},
    "soup": {"area": 80000, "unit": "ml", "avg_volume": 300, "density": 1.0, "countable": False},
    "cereal": {"area": 40000, "unit": "g", "avg_weight": 100, "density": 0.2, "countable": False},
    "flour": {"area": 40000, "unit": "g", "avg_weight": 500, "density": 0.5, "countable": False},
    "sugar": {"area": 35000, "unit": "g", "avg_weight": 500, "density": 0.9, "countable": False},
    "salt": {"area": 20000, "unit": "g", "avg_weight": 250, "density": 1.2, "countable": False},
    "oil": {"area": 30000, "unit": "ml", "avg_volume": 500, "density": 0.9, "countable": False},
}

DEFAULT_UNIT_VOLUME = "ml"
DEFAULT_UNIT_COUNT = "pieces"
DEFAULT_UNIT_WEIGHT = "g"

def get_object_detection_model():
    if "object_detection" not in _models:
        model_name = "facebook/detr-resnet-50"
        feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
        model = AutoModelForObjectDetection.from_pretrained(model_name)
        _models["object_detection"] = (feature_extractor, model)
    
    return _models["object_detection"]

def get_image_classification_model():
    if "image_classification" not in _models:
        model_name = "nateraw/food"
        processor = AutoProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)
        _models["image_classification"] = (processor, model)
    
    return _models["image_classification"]

def create_masks_from_boxes(image_np: np.ndarray, boxes: List[List[float]]) -> List[np.ndarray]:
    height, width = image_np.shape[:2]
    masks = []
    
    for box in boxes:
        x1, y1, x2, y2 = [int(coord) for coord in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 1
        masks.append(mask)
    
    return masks

def count_instances(detections: List[Dict], iou_threshold: float = 0.5) -> Dict[str, int]:
    detections_by_name = defaultdict(list)
    for detection in detections:
        detections_by_name[detection["name"]].append(detection["box_coordinates"])
    counts = {}
    
    for name, boxes in detections_by_name.items():
        sorted_boxes = boxes.copy()
        kept_boxes = []
        while sorted_boxes:
            current_box = sorted_boxes.pop(0)
            kept_boxes.append(current_box)
            filtered_boxes = []
            for box in sorted_boxes:
                if calculate_iou(current_box, box) < iou_threshold:
                    filtered_boxes.append(box)
            
            sorted_boxes = filtered_boxes
        
        counts[name] = len(kept_boxes)
    
    return counts

def calculate_iou(box1: List[float], box2: List[float]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    intersection_area = max(0, x2 - x1) * max(0, y2 - y1)

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = box1_area + box2_area - intersection_area
    
    if union_area == 0:
        return 0
    return intersection_area / union_area

def estimate_specific_quantity(item_name: str, box_area: float, image_area: float, 
                              depth_info: Optional[Tuple] = None, mask: Optional[np.ndarray] = None,
                              count: int = 1) -> str:
    normalized_name = item_name.lower()
    
    ref_match = None
    for ref_name, ref_data in REFERENCE_SIZES.items():
        if ref_name in normalized_name:
            ref_match = (ref_name, ref_data)
            break
    if ref_match:
        ref_name, reference = ref_match
        if reference["countable"] and count > 1:
            return f"{count} {ref_name}" + ("s" if count > 1 else "")
        if depth_info and mask is not None and USE_DEPTH_ESTIMATION:
            depth_map, _ = depth_info
            relative_volume = depth_estimator.estimate_volume(depth_map, mask)
            if reference["unit"] == "ml":
                volume_scale_factor = 2000 
                volume = round(relative_volume * volume_scale_factor / 50) * 50 
                
                if volume >= 1000:
                    return f"{volume/1000:.1f} liter{'s' if volume > 1000 else ''}"
                return f"{volume}ml"
                
            elif reference["unit"] == "g": 
                weight_scale_factor = 1000 * reference["density"]  
                weight = round(relative_volume * weight_scale_factor / 25) * 25 
                
                if weight >= 1000:
                    return f"{weight/1000:.1f}kg"
                return f"{weight}g"
            
            elif reference["unit"] == "whole": 
                if count > 1:
                    return f"{count} {ref_name}" + ("s" if count > 1 else "")
                
                weight_scale_factor = 500 * reference["density"]
                weight = round(relative_volume * weight_scale_factor / 10) * 10
                
                if reference["avg_weight"] > 0:
                    count_estimate = max(1, round(weight / reference["avg_weight"]))
                    if count_estimate > 1:
                        return f"{count_estimate} {ref_name}s"
                
                return f"1 {ref_name}"
            
        size_ratio = box_area / reference["area"]

        if reference["unit"] == "whole":
            if count <= 1:
                count = max(1, round(size_ratio))
            return f"{count} {ref_name}" + ("s" if count > 1 else "")
        
        elif reference["unit"] == "ml":
            volume = round(reference["avg_volume"] * size_ratio / 50) * 50 
            if volume >= 1000:
                return f"{volume/1000:.1f} liter{'s' if volume > 1000 else ''}"
            return f"{volume}ml"
        
        elif reference["unit"] == "g":
            weight = round(reference["avg_weight"] * size_ratio / 25) * 25  
            if weight >= 1000:
                return f"{weight/1000:.1f}kg"
            return f"{weight}g"
        
        elif reference["unit"] == "slice":
            slices = max(1, round(size_ratio))
            return f"{slices} slice{'s' if slices > 1 else ''} of {ref_name}"
    
    relative_size = box_area / image_area
    
    if relative_size < 0.1 and count <= 1:  
        count_guess = max(1, round(10 * relative_size))
        return f"{count_guess} {item_name.lower()}" + ("s" if count_guess > 1 else "")
    elif count > 1:
        return f"{count} {item_name.lower()}" + ("s" if count > 1 else "")
    
    elif "bottle" in normalized_name or "milk" in normalized_name or "juice" in normalized_name or "liquid" in normalized_name:
        volume = round(500 * relative_size * 10 / 50) * 50  
        if volume >= 1000:
            return f"{volume/1000:.1f} liter{'s' if volume > 1000 else ''}"
        return f"{volume}ml"
    
    else:
        weight = round(500 * relative_size * 10 / 25) * 25 
        if weight >= 1000:
            return f"{weight/1000:.1f}kg"
        return f"{weight}g"

def analyze_image_with_local_model(image_bytes: bytes) -> Dict[str, Any]:
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    image_np = np.array(pil_image)
    
    depth_info = None
    if USE_DEPTH_ESTIMATION:
        try:
            depth_map, colored_depth = depth_estimator.estimate_depth(image_bytes)
            depth_info = (depth_map, colored_depth)
        except Exception as e:
            print(f"Depth estimation failed: {str(e)}")
    
    feature_extractor, object_model = get_object_detection_model()
    inputs = feature_extractor(images=pil_image, return_tensors="pt")
    outputs = object_model(**inputs)
    
    target_sizes = torch.tensor([pil_image.size[::-1]])
    results = feature_extractor.post_process_object_detection(
        outputs, target_sizes=target_sizes, threshold=0.7)[0]
    
    food_categories = [
        "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", 
        "donut", "cake", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
        "fruit", "vegetable", "milk", "cheese", "egg", "meat", "fish", "bread", "pasta",
        "rice", "cereal", "yogurt", "butter", "oil", "sauce", "soup"
    ]
    
    detected_items = []
    image_area = pil_image.width * pil_image.height
    boxes_by_class = defaultdict(list)
    
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        label_name = object_model.config.id2label[label.item()]
        if label_name in food_categories or "food" in label_name.lower():
            box_coords = box.tolist()
            boxes_by_class[label_name].append(box_coords)
            
            box_width = box_coords[2] - box_coords[0]
            box_height = box_coords[3] - box_coords[1]
            box_area = box_width * box_height
            
            detected_items.append({
                "name": label_name,
                "confidence": float(score.item()),
                "estimated_quantity": "calculating...", 
                "box_coordinates": box_coords
            })
    
    all_masks = []
    if depth_info:
        for item in detected_items:
            mask = np.zeros((pil_image.height, pil_image.width), dtype=np.uint8)
            box = item["box_coordinates"]
            x1, y1, x2, y2 = [int(coord) for coord in box]
            mask[y1:y2, x1:x2] = 1
            all_masks.append(mask)
    
    object_counts = count_instances(detected_items)
    
    for i, item in enumerate(detected_items):
        box_coords = item["box_coordinates"]
        box_width = box_coords[2] - box_coords[0]
        box_height = box_coords[3] - box_coords[1]
        box_area = box_width * box_height
        
        mask = all_masks[i] if i < len(all_masks) and depth_info else None
        count = object_counts.get(item["name"], 1)
        
        item["estimated_quantity"] = estimate_specific_quantity(
            item["name"], box_area, image_area, depth_info, mask, count
        )
    
    if not detected_items:
        processor, classification_model = get_image_classification_model()
        inputs = processor(images=pil_image, return_tensors="pt")
        outputs = classification_model(**inputs)
        predicted_class_idx = outputs.logits.argmax(-1).item()
        predicted_class = classification_model.config.id2label[predicted_class_idx]
        
        mask = np.ones((pil_image.height, pil_image.width), dtype=np.uint8)
        quantity = estimate_specific_quantity(
            predicted_class, image_area * 0.5, image_area, depth_info, mask
        )
        
        detected_items.append({
            "name": predicted_class,
            "confidence": float(outputs.logits.softmax(-1).max().item()),
            "estimated_quantity": quantity,
            "box_coordinates": [0, 0, pil_image.width, pil_image.height]
        })
    
    result = {
        "ingredients": detected_items,
        "model_used": "local_huggingface_models"
    }
    
    if depth_info:
        result["depth_estimation_used"] = True
    
    return result

def analyze_image_with_openai(image_bytes: bytes) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set")
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "This is an image of a fridge or food items. Please identify all food ingredients visible in this image. For each ingredient, provide: 1) the name of the ingredient, 2) an estimated specific quantity (e.g., '3 apples', '500ml milk', '250g cheese', NOT vague terms like 'medium amount'), and 3) a confidence score from 0-1. Format your response as a JSON object with an array called 'ingredients' where each item has fields 'name', 'estimated_quantity', and 'confidence'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"OpenAI API error: {response.text}")
    
    response_text = response.json()["choices"][0]["message"]["content"]
    
    import json
    import re
    
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            result["model_used"] = "openai_gpt4_vision"
            return result
        except json.JSONDecodeError:
            pass
    
    return {
        "ingredients": [{"name": "unknown", "estimated_quantity": "unknown", "confidence": 0}],
        "model_used": "openai_gpt4_vision",
        "error": "Failed to parse OpenAI response"
    }

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    if MODEL_TYPE == "openai" and USE_OPENAI:
        return analyze_image_with_openai(image_bytes)
    else:
        return analyze_image_with_local_model(image_bytes) 