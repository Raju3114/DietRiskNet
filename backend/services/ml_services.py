import os
from typing import Union
import torch
import torchvision.transforms as T
from PIL import Image
import io
from ultralytics import YOLO
import timm
from backend.config import settings
from backend.utils.logger import ml_logger

class FoodDetectionService:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            ml_logger.info(f"Loading YOLOv8 detector from {settings.YOLO_MODEL_PATH}")
            self.model = YOLO(settings.YOLO_MODEL_PATH)
            ml_logger.info("YOLOv8 detector loaded successfully.")
        except Exception as e:
            ml_logger.error(f"Failed to load YOLOv8 detector: {e}")
            raise e

    def detect(self, image_path_or_bytes: Union[str, bytes]) -> list:
        """
        Runs YOLOv8 detector.
        Returns a list of dicts: [{"name": name, "confidence": conf, "box": (x1, y1, x2, y2)}]
        """
        if self.model is None:
            self.load_model()
        try:
            # Load image
            if isinstance(image_path_or_bytes, str):
                img = Image.open(image_path_or_bytes)
            else:
                img = Image.open(io.BytesIO(image_path_or_bytes))

            # Run inference
            results = self.model(img)
            detections = []
            
            # YOLO results is a list of Results objects
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # coords
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names[cls_id]
                    
                    detections.append({
                        "name": cls_name,
                        "confidence": conf,
                        "box": (x1, y1, x2, y2)
                    })
            
            ml_logger.info(f"YOLOv8 detected {len(detections)} objects.")
            return detections
        except Exception as e:
            ml_logger.error(f"Error in YOLOv8 inference: {e}")
            raise e


class FoodClassificationService:
    def __init__(self):
        self.model = None
        self.class_names = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_model()

    def load_model(self):
        try:
            model_file = settings.FOOD_CLASSIFIER_MODEL
            model_path = os.path.join(settings.MODELS_DIR, model_file)
            
            # Fallback to B0 if B3 model is missing
            if not os.path.exists(model_path):
                fallback_file = "DietRiskNet_FoodClassifier_EfficientNetB0.pth"
                fallback_path = os.path.join(settings.MODELS_DIR, fallback_file)
                if os.path.exists(fallback_path):
                    ml_logger.warning(f"Configured model {model_file} not found at {model_path}. Falling back to {fallback_file}.")
                    model_file = fallback_file
                    model_path = fallback_path
                else:
                    raise FileNotFoundError(f"Neither configured model {model_file} nor fallback B0 model found in {settings.MODELS_DIR}.")
            
            ml_logger.info(f"Loading Food Classifier ({model_file}) from {model_path} on {self.device}")
            
            checkpoint = torch.load(model_path, map_location=self.device)
            self.class_names = checkpoint.get("class_names", [])
            state_dict = checkpoint["model_state_dict"]
            
            # Dynamically determine the architecture (B0 vs B3) based on state dict shape
            # B3 stem conv_stem.weight out_channels is 40, B0 is 32.
            arch = "efficientnet_b0"
            if "conv_stem.weight" in state_dict:
                out_channels = state_dict["conv_stem.weight"].shape[0]
                if out_channels == 40:
                    arch = "efficientnet_b3"
            elif "features.0.0.weight" in state_dict:
                out_channels = state_dict["features.0.0.weight"].shape[0]
                if out_channels == 40:
                    arch = "efficientnet_b3"
                    
            ml_logger.info(f"Detected architecture: {arch} based on model state dict shape.")
            
            self.model = timm.create_model(arch, num_classes=len(self.class_names))
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            
            # Set target crop size based on loaded architecture
            self.crop_size = 300 if arch == "efficientnet_b3" else 224
            
            ml_logger.info(f"Classifier model loaded successfully with {len(self.class_names)} classes.")
        except Exception as e:
            ml_logger.error(f"Failed to load Classifier: {e}")
            raise e

    def classify(self, crop_image_bytes: bytes) -> dict:
        """
        Classifies a cropped food image.
        Returns {"class_name": class_name, "confidence": conf}
        """
        if self.model is None:
            self.load_model()
        try:
            # Load and preprocess crop
            img = Image.open(io.BytesIO(crop_image_bytes)).convert("RGB")
            
            # Set crop size based on loaded architecture
            crop_size = getattr(self, "crop_size", 224)
            
            transforms = T.Compose([
                T.Resize((crop_size, crop_size)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            input_tensor = transforms(img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                conf, idx = torch.max(probabilities, dim=1)
                
                confidence_score = float(conf.item())
                class_index = int(idx.item())
                predicted_class = self.class_names[class_index]
                
            ml_logger.info(f"Classified food: {predicted_class} with confidence {confidence_score:.4f}")
            return {
                "class_name": predicted_class,
                "confidence": confidence_score
            }
        except Exception as e:
            ml_logger.error(f"Error in food classification inference: {e}")
            raise e
