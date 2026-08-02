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
  display_name?: string;
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
  // False when the recognised food has no nutrition record (nutrients are 0).
  nutrition_available?: boolean;
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

export interface NutritionGoal {
  id: string;
  title: string;
  progress: number;
  status: 'on-track' | 'in-progress' | 'needs-attention';
}

export interface NutritionAnalytics {
  meals_analyzed: number;
  meals_this_week: number;
  avg_calories: number;
  avg_protein: number;
  avg_carbs: number;
  avg_fats: number;
  avg_sodium: number;
  avg_fiber: number;
  avg_dci: number | null;  // null = insufficient data (genuine DCI is never 0.0)
  avg_nis: number;
  highest_risk: { name: string; value: number } | null;
  best_meal: { date: string; dci: number } | null;
  meal_needing_improvement: { date: string; nis: number } | null;
  most_common_food: string | null;
  patterns: string[];
  positive_habits: string[];
  habits_to_improve: string[];
  dci_trend: { delta: number; direction: 'improved' | 'declined' | 'stable' } | null;
  risk_trend: { name: string; delta: number; direction: string } | null;
  goals: NutritionGoal[];
  nutrient_deficiencies: string[];
}

export interface AIDietitian {
  summary: string;
  meal_quality: string;
  health_score: number;
  health_level: string;
  health_explanation: string;
  risk_explanation: string;
  recommendations: string[];
  healthier_alternatives: string[];
  warnings: string[];
  follow_up_questions: string[];
}

export interface MealAnalysis {
  meal_id: number;
  image_path?: string;
  items: MealItem[];
  nutrition: NutritionData;
  // Nullable: null = insufficient data (no item had usable nutrition).
  dci?: number | null;
  dci_level?: string | null;
  nis?: number | null;
  nis_level?: string | null;
  predictions?: DiseasePredictions | null;
  fusion?: RiskFusion | null;
  recommendations: Recommendation[];
  ai_dietitian?: AIDietitian | null;
  created_at: string;
}
