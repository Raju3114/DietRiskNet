from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import Dict, Any, List
from backend.database.models import (
    User, UserSetting, Meal, MealItem, MealNutrition, 
    DiseasePrediction, RiskFusionResult, Recommendation, DietHistory
)
from backend.schemas.schemas import UserSettingUpdate
from backend.utils.logger import db_logger

class ProfileService:
    def get_profile(self, user_id: int, db: Session) -> User:
        return db.query(User).filter(User.id == user_id).first()

    def update_profile(self, user_id: int, full_name: str, db: Session) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.full_name = full_name
            db.commit()
            db.refresh(user)
        return user

    def get_settings(self, user_id: int, db: Session) -> UserSetting:
        setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
        if not setting:
            # Create default settings
            setting = UserSetting(user_id=user_id)
            db.add(setting)
            db.commit()
            db.refresh(setting)
        return setting

    def update_settings(self, user_id: int, data: UserSettingUpdate, db: Session) -> UserSetting:
        setting = self.get_settings(user_id, db)
        
        update_data = data.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(setting, key, val)
            
        db.commit()
        db.refresh(setting)
        return setting


class MealService:
    def create_meal(self, user_id: int, image_path: str, notes: str, db: Session) -> Meal:
        meal = Meal(
            user_id=user_id,
            image_path=image_path,
            notes=notes,
            created_at=datetime.utcnow()
        )
        db.add(meal)
        db.commit()
        db.refresh(meal)
        return meal

    def add_meal_items_and_aggregate(self, meal_id: int, items_data: List[Dict[str, Any]], db: Session) -> MealNutrition:
        # Delete any existing items if re-analyzing
        db.query(MealItem).filter(MealItem.meal_id == meal_id).delete()
        
        # Insert new items
        db_items = []
        agg = {
            "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fats": 0.0,
            "sugar": 0.0, "fiber": 0.0, "sodium": 0.0, "calcium": 0.0,
            "iron": 0.0, "vitamin_c": 0.0, "folate": 0.0
        }
        
        for item in items_data:
            box = item.get("bounding_box") or {}
            db_item = MealItem(
                meal_id=meal_id,
                name=item["name"],
                confidence=item.get("confidence", 1.0),
                x1=box.get("x1"),
                y1=box.get("y1"),
                x2=box.get("x2"),
                y2=box.get("y2"),
                weight_g=item.get("weight_g", 100.0),
                calories=item.get("calories", 0.0),
                protein=item.get("protein", 0.0),
                carbs=item.get("carbs", 0.0),
                fats=item.get("fats", 0.0),
                sugar=item.get("sugar", 0.0),
                fiber=item.get("fiber", 0.0),
                sodium=item.get("sodium", 0.0),
                calcium=item.get("calcium", 0.0),
                iron=item.get("iron", 0.0),
                vitamin_c=item.get("vitamin_c", 0.0),
                folate=item.get("folate", 0.0),
            )
            db_items.append(db_item)
            db.add(db_item)
            
            # Aggregate values
            for k in agg.keys():
                agg[k] += item.get(k, 0.0)
                
        # Save aggregated nutrition
        db.query(MealNutrition).filter(MealNutrition.meal_id == meal_id).delete()
        nutrition = MealNutrition(meal_id=meal_id, **agg)
        db.add(nutrition)
        
        # Link to DietHistory
        history_entry = db.query(DietHistory).filter(DietHistory.meal_id == meal_id).first()
        if not history_entry:
            meal = db.query(Meal).filter(Meal.id == meal_id).first()
            history_entry = DietHistory(
                user_id=meal.user_id,
                meal_id=meal_id,
                logged_date=meal.created_at
            )
            db.add(history_entry)

        db.commit()
        db.refresh(nutrition)
        return nutrition

    def save_pipeline_results(self, meal_id: int, dci: float, dci_level: str, 
                              nis: float, nis_level: str, 
                              predictions_dict: dict, fusion_dict: dict, 
                              recommendations_list: List[Dict[str, str]], db: Session):
        # Update meal model indices
        meal = db.query(Meal).filter(Meal.id == meal_id).first()
        meal.dci = dci
        meal.dci_level = dci_level
        meal.nis = nis
        meal.nis_level = nis_level
        meal.risk_fusion_score = fusion_dict["fused_score"]
        meal.risk_fusion_level = fusion_dict["risk_level"]
        
        # Save disease predictions
        db.query(DiseasePrediction).filter(DiseasePrediction.meal_id == meal_id).delete()
        pred = DiseasePrediction(
            meal_id=meal_id,
            diabetes_risk=predictions_dict["diabetes_risk"],
            obesity_risk=predictions_dict["obesity_risk"],
            hypertension_risk=predictions_dict["hypertension_risk"],
            deficiency_risk=predictions_dict["deficiency_risk"]
        )
        db.add(pred)
        
        # Save fusion result
        db.query(RiskFusionResult).filter(RiskFusionResult.meal_id == meal_id).delete()
        fusion = RiskFusionResult(
            meal_id=meal_id,
            fused_score=fusion_dict["fused_score"],
            risk_level=fusion_dict["risk_level"]
        )
        db.add(fusion)
        
        # Save recommendations
        db.query(Recommendation).filter(Recommendation.meal_id == meal_id).delete()
        for rec in recommendations_list:
            db_rec = Recommendation(
                meal_id=meal_id,
                category=rec["category"],
                content=rec["content"],
                explanation=rec["explanation"]
            )
            db.add(db_rec)
            
        db.commit()


class DashboardService:
    def get_dashboard_data(self, user_id: int, db: Session) -> dict:
        # Today's timeframe
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's meals
        today_meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.created_at >= today_start
        ).all()
        
        # Get user settings for RDI comparison
        setting = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
        rdi = {
            "Calories": 2000.0, "Protein": 60.0, "Carbs": 300.0, "Fat": 65.0, "Sodium": 2300.0, "Fiber": 30.0
        }
        if setting and setting.rdi_custom:
            # Merge custom values
            rdi.update(setting.rdi_custom)
            
        # Aggregate today's nutrition
        daily_agg = {
            "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fats": 0.0,
            "sugar": 0.0, "fiber": 0.0, "sodium": 0.0, "calcium": 0.0,
            "iron": 0.0, "vitamin_c": 0.0, "folate": 0.0
        }
        
        for m in today_meals:
            if m.nutrition:
                for k in daily_agg.keys():
                    daily_agg[k] += getattr(m.nutrition, k, 0.0)

        # Calculate percentages of RDI
        pct = {
            "Calories": (daily_agg["calories"] / rdi["Calories"]) * 100 if rdi["Calories"] > 0 else 0,
            "Protein": (daily_agg["protein"] / rdi["Protein"]) * 100 if rdi["Protein"] > 0 else 0,
            "Carbs": (daily_agg["carbs"] / rdi["Carbs"]) * 100 if rdi["Carbs"] > 0 else 0,
            "Fat": (daily_agg["fats"] / rdi["Fat"]) * 100 if rdi["Fat"] > 0 else 0,
            "Sodium": (daily_agg["sodium"] / rdi["Sodium"]) * 100 if rdi["Sodium"] > 0 else 0,
            "Fiber": (daily_agg["fiber"] / rdi["Fiber"]) * 100 if rdi["Fiber"] > 0 else 0,
        }
        
        # Get latest indexes (from latest meal)
        latest_meal = db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.created_at.desc()).first()
        
        dci = latest_meal.dci if latest_meal else 1.0
        dci_level = latest_meal.dci_level if latest_meal else "High Consistency"
        nis = latest_meal.nis if latest_meal else 0.0
        nis_level = latest_meal.nis_level if latest_meal else "Balanced Diet"
        fusion_score = latest_meal.risk_fusion_score if latest_meal else 0.0
        fusion_level = latest_meal.risk_fusion_level if latest_meal else "Low"
        
        # Get recent 5 meals
        recent_db_meals = db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.created_at.desc()).limit(5).all()
        recent_meals = []
        for rm in recent_db_meals:
            recent_meals.append({
                "id": rm.id,
                "created_at": rm.created_at,
                "image_path": rm.image_path,
                "calories": rm.nutrition.calories if rm.nutrition else 0.0,
                "items_count": len(rm.items),
                "risk_score": rm.risk_fusion_score or 0.0
            })

        # Get latest recommendations
        recs = []
        if latest_meal:
            db_recs = db.query(Recommendation).filter(Recommendation.meal_id == latest_meal.id).all()
            for r in db_recs:
                recs.append({
                    "category": r.category,
                    "content": r.content,
                    "explanation": r.explanation
                })
        else:
            recs.append({
                "category": "General Health",
                "content": "Log your first meal to receive personalized, disease-risk-aware suggestions.",
                "explanation": "ExplainDiet suggestions generate automatically after recognizing your food selections."
            })
            
        return {
            "daily_aggregated": daily_agg,
            "daily_percentage_rdi": pct,
            "dci": dci,
            "dci_level": dci_level,
            "nis": nis,
            "nis_level": nis_level,
            "fused_risk_score": fusion_score,
            "fused_risk_level": fusion_level,
            "recent_meals": recent_meals,
            "recommendations": recs
        }


class HistoryService:
    def get_history(self, user_id: int, db: Session) -> List[dict]:
        meals = db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.created_at.desc()).all()
        history = []
        for m in meals:
            items = []
            for it in m.items:
                items.append({
                    "name": it.name,
                    "confidence": it.confidence,
                    "weight_g": it.weight_g
                })
            history.append({
                "id": m.id,
                "created_at": m.created_at,
                "image_path": m.image_path,
                "dci": m.dci,
                "nis": m.nis,
                "risk_score": m.risk_fusion_score,
                "risk_level": m.risk_fusion_level,
                "calories": m.nutrition.calories if m.nutrition else 0.0,
                "protein": m.nutrition.protein if m.nutrition else 0.0,
                "carbs": m.nutrition.carbs if m.nutrition else 0.0,
                "fats": m.nutrition.fats if m.nutrition else 0.0,
                "items": items
            })
        return history


class AnalyticsService:
    def get_trends(self, user_id: int, days: int, db: Session) -> List[dict]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query meals in period
        meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.created_at >= start_date
        ).order_by(Meal.created_at.asc()).all()
        
        # Group nutrition & predictions by date YYYY-MM-DD
        daily_trends = {}
        for m in meals:
            day_str = m.created_at.strftime("%Y-%m-%d")
            if day_str not in daily_trends:
                daily_trends[day_str] = {
                    "date": day_str,
                    "calories": 0.0,
                    "protein": 0.0,
                    "carbs": 0.0,
                    "fats": 0.0,
                    "dci": m.dci or 1.0,
                    "nis": m.nis or 0.0,
                    # Fallback default risks if prediction missing
                    "diabetes_risk": m.predictions.diabetes_risk if m.predictions else 0.1,
                    "obesity_risk": m.predictions.obesity_risk if m.predictions else 0.1,
                    "hypertension_risk": m.predictions.hypertension_risk if m.predictions else 0.1,
                    "deficiency_risk": m.predictions.deficiency_risk if m.predictions else 0.1,
                    "meal_count": 0
                }
            
            data = daily_trends[day_str]
            if m.nutrition:
                data["calories"] += m.nutrition.calories
                data["protein"] += m.nutrition.protein
                data["carbs"] += m.nutrition.carbs
                data["fats"] += m.nutrition.fats
            
            data["meal_count"] += 1
            # Keep latest indices and prediction of the day
            data["dci"] = m.dci or data["dci"]
            data["nis"] = m.nis or data["nis"]
            if m.predictions:
                data["diabetes_risk"] = m.predictions.diabetes_risk
                data["obesity_risk"] = m.predictions.obesity_risk
                data["hypertension_risk"] = m.predictions.hypertension_risk
                data["deficiency_risk"] = m.predictions.deficiency_risk

        return list(daily_trends.values())

# Singleton instances of services
profile_service = ProfileService()
meal_db_service = MealService()
dashboard_service = DashboardService()
history_service = HistoryService()
analytics_service = AnalyticsService()
