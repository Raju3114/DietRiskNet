import json
import os
from backend.config import settings
from backend.utils.logger import app_logger

class RiskFusionService:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(settings.RISK_FUSION_CONFIG_PATH):
                with open(settings.RISK_FUSION_CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                app_logger.info("Loaded Risk Fusion configurations successfully.")
            else:
                app_logger.error(f"Risk Fusion Config not found at {settings.RISK_FUSION_CONFIG_PATH}")
        except Exception as e:
            app_logger.error(f"Failed to load Risk Fusion config: {e}")

    def fuse(self, dci: float, nis: float, diabetes_risk: float, obesity_risk: float, 
             hypertension_risk: float, deficiency_risk: float) -> tuple:
        """
        Calculates unified fused risk score from weights in config file.
        Returns (fused_score, risk_level)
        """
        weights = self.config.get("weights", {
            "DCI": 0.25,
            "NIS": 0.25,
            "Diabetes": 0.2,
            "Obesity": 0.15,
            "Hypertension": 0.1,
            "Deficiency": 0.05
        })
        
        # Consistent diet (high DCI) reduces risk. So risk from inconsistency is 1 - DCI.
        dci_risk = 1.0 - dci
        
        fused_score = (
            weights.get("DCI", 0.25) * dci_risk +
            weights.get("NIS", 0.25) * nis +
            weights.get("Diabetes", 0.2) * diabetes_risk +
            weights.get("Obesity", 0.15) * obesity_risk +
            weights.get("Hypertension", 0.1) * hypertension_risk +
            weights.get("Deficiency", 0.05) * deficiency_risk
        )
        
        # Bounded score
        fused_score = float(max(0.0, min(1.0, fused_score)))
        
        # Categorize level
        if fused_score <= 0.25:
            risk_level = "Low"
        elif fused_score <= 0.50:
            risk_level = "Moderate"
        elif fused_score <= 0.75:
            risk_level = "High"
        else:
            risk_level = "Critical"
            
        return fused_score, risk_level
