import torch
import cv2
import numpy as np
from PIL import Image
import io
import os
import urllib.request
from torch import nn
import torchvision.transforms as transforms

class DepthEstimator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None
        
    def download_model(self, model_url, model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        urllib.request.urlretrieve(model_url, model_path)
        
    def load_model(self):
        if self.model is None:
            model_dir = os.path.join(os.path.expanduser("~"), ".whatthefridge", "models")
            model_path = os.path.join(model_dir, "monodepth_net.pt")
            
            if not os.path.exists(model_path):
                model_url = "https://github.com/intel-isl/MiDaS/releases/download/v2_1/model-small-70d6b9c8.pt"
                self.download_model(model_url, model_path)
            
            self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", pretrained=False)
            if os.path.exists(model_path):
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
    
    def estimate_depth(self, image_bytes):
        try:
            self.load_model()
            
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            original_size = image.size  # Save original image size
            
            # Resize for model input
            resized_image = image.resize((384, 384), Image.LANCZOS)
            input_tensor = self.transform(resized_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                prediction = self.model(input_tensor)
            
            depth_map = prediction.squeeze().cpu().numpy()
            normalized_depth = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())
            
            # Resize depth map back to original image dimensions
            depth_map_resized = cv2.resize(normalized_depth, (original_size[0], original_size[1]), 
                                          interpolation=cv2.INTER_LINEAR)
            
            colored_depth = cv2.applyColorMap(
                (depth_map_resized * 255).astype(np.uint8),
                cv2.COLORMAP_JET
            )
            
            return depth_map_resized, colored_depth
        except Exception as e:
            print(f"Depth estimation error: {str(e)}")
            # Return dummy depth map with same dimensions as original image
            dummy_depth = np.ones((image.height, image.width), dtype=np.float32) * 0.5
            dummy_color = np.ones((image.height, image.width, 3), dtype=np.uint8) * 128
            return dummy_depth, dummy_color
    
    def estimate_volume(self, depth_map, mask, real_world_reference=None):
        if mask.sum() == 0:
            return 0
        
        if depth_map.shape != mask.shape:
            mask_resized = cv2.resize(mask, (depth_map.shape[1], depth_map.shape[0]), 
                                     interpolation=cv2.INTER_NEAREST)
            object_depth = depth_map * mask_resized
            object_depth = object_depth[mask_resized > 0]
            pixel_count = mask_resized.sum()
        else:
            object_depth = depth_map * mask
            object_depth = object_depth[mask > 0]
            pixel_count = mask.sum()
        
        if len(object_depth) == 0:
            return 0
            
        avg_depth = object_depth.mean()
        
        if real_world_reference:
            pixels_per_cm = real_world_reference
            area_cm2 = pixel_count / (pixels_per_cm ** 2)
            depth_scaling_factor = 50.0
            depth_cm = avg_depth * depth_scaling_factor
            volume_cm3 = area_cm2 * depth_cm
            return volume_cm3
        
        return pixel_count * avg_depth

depth_estimator = DepthEstimator() 