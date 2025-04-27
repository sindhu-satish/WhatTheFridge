import torch
import cv2
import numpy as np
from PIL import Image
import io
from transformers import DPTForDepthEstimation, DPTFeatureExtractor

class DepthEstimator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.feature_extractor = None
        
    def load_model(self):
        if self.model is None:
            model_name = "Intel/dpt-hybrid-midas"
            self.feature_extractor = DPTFeatureExtractor.from_pretrained(model_name)
            self.model = DPTForDepthEstimation.from_pretrained(model_name)
            self.model.to(self.device)
        
    def estimate_depth(self, image_bytes):
        self.load_model()
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self.feature_extractor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predicted_depth = outputs.predicted_depth
        
        depth_map = predicted_depth.squeeze().cpu().numpy()
        normalized_depth = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
        colored_depth = cv2.applyColorMap(
            (normalized_depth * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        return normalized_depth, colored_depth
    
    def estimate_volume(self, depth_map, mask, real_world_reference=None):
        if mask.sum() == 0:
            return 0
        
        object_depth = depth_map * mask
        object_depth = object_depth[mask > 0]
        avg_depth = object_depth.mean()
        pixel_count = mask.sum()
        
        if real_world_reference:
            pixels_per_cm = real_world_reference
            area_cm2 = pixel_count / (pixels_per_cm ** 2)
            depth_scaling_factor = 50.0 
            depth_cm = avg_depth * depth_scaling_factor
            volume_cm3 = area_cm2 * depth_cm
            return volume_cm3
        
        return pixel_count * avg_depth

depth_estimator = DepthEstimator() 