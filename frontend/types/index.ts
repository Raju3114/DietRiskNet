export interface User {
  id: number;
  email: string;
  full_name?: string;
}

export interface UserSettings {
  age: number;
  gender: string;
  height: number;
  weight: number;
  activity_level: string;
  existing_conditions: string[];
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface MealItem {
  id?: number;
  name: string;
  confidence: number;
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  weight_g: number;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  sugar: number;
  fiber: number;
  sodium: number;
  calcium: number;
  iron: number;
  vitamin_c: number;
  folate: number;
}

export interface NutritionData {
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  sugar: number;
  fiber: number;
  sodium: number;
  calcium: number;
  iron: number;
  vitamin_c: number;
  folate: number;
}

export interface DiseasePredictions {
  diabetes_risk: number;
  obesity_risk: number;
  hypertension_risk: number;
  deficiency_risk: number;
}

export interface RiskFusion {
  fused_score: number;
  risk_level: string;
}

export interface Recommendation {
  category: string;
  content: string;
  explanation: string;
}

export interface MealAnalysis {
  meal_id: number;
  image_path?: string;
  items: MealItem[];
  nutrition: NutritionData;
  dci: number;
  dci_level: string;
  nis: number;
  nis_level: string;
  predictions: DiseasePredictions;
  fusion: RiskFusion;
  recommendations: Recommendation[];
  created_at: string;
}
