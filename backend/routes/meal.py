import os
import shutil
import uuid
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.routes.deps import get_current_user
from backend.database.models import User, MealItem
from backend.config import settings
from backend.schemas.schemas import (
    FoodDetectionResponse, FoodClassificationResponse, NutritionAnalysisRequest,
    NutritionAnalysisResponse, CalculateDCIRequest, CalculateDCIResponse,
    CalculateNISRequest, CalculateNISResponse, MealAnalysisResponse, MealItemBase, BoundingBox
)
from backend.services.ml_services import detector_service, classifier_service
from backend.services.nutrition_service import nutrition_service
from backend.services.indices_services import dci_service, nis_service
from backend.services.prediction_service import prediction_service
from backend.services.risk_fusion_service import fusion_service
from backend.services.recommendation_service import explain_diet_service
from backend.services.user_services import meal_db_service
from backend.services.meal_ai_service import meal_ai_service
from backend.utils.image_utils import crop_image
from backend.utils.logger import api_logger

def _ensure_valid_image(image_path: str) -> None:
    """Validate that *image_path* is a decodable image.

    Raises a 400 with a safe, user-friendly message on corrupt / invalid
    image files.  Never leaks internal paths, Python exceptions or library
    (e.g. PIL/DLL) details to the client.
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception:
        api_logger.warning(f"Rejected invalid/corrupt image: {image_path}")
        try:
            os.remove(image_path)  # clean up the bad upload
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to process this image. Please upload a valid JPG, JPEG, or PNG.",
        )


router = APIRouter(prefix="", tags=["Meal Pipeline"])

DEFAULT_SERVING_WEIGHTS = {
    "idli": 60.0,
    "masala_dosa": 180.0,
    "plain_dosa": 150.0,
    "chapati": 40.0,
    "rice": 180.0,
    "fried_rice": 250.0,
    "burger": 220.0,
    "pizza": 150.0,
    "samosa": 100.0,
    "jalebi": 50.0,
    "tea": 150.0,
    "coffee": 150.0
}

@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPG, JPEG, PNG, and WEBP are supported."
        )
    try:
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        api_logger.info(f"User {current_user.email} uploaded file saved to {file_path}")
        # Return relative or absolute path
        return {"file_path": file_path, "filename": unique_filename}
    except Exception as e:
        api_logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/detect-food", response_model=FoodDetectionResponse)
def detect_food(file_path: str = Form(...), current_user: User = Depends(get_current_user)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found.")
    _ensure_valid_image(file_path)

    try:
        detections = detector_service.detect(file_path)
        items = []
        for d in detections:
            x1, y1, x2, y2 = d["box"]
            items.append(MealItemBase(
                name=d["name"],
                confidence=d["confidence"],
                bounding_box=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
            ))
        return {"detections": items}
    except Exception as e:
        api_logger.error(f"Food detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    finally:
        detector_service.unload()

@router.post("/classify-food", response_model=FoodClassificationResponse)
def classify_food(file_path: str = Form(...), x1: float = Form(...), y1: float = Form(...), x2: float = Form(...), y2: float = Form(...), current_user: User = Depends(get_current_user)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found.")
    _ensure_valid_image(file_path)

    try:
        crop_bytes = crop_image(file_path, (x1, y1, x2, y2))
        res = classifier_service.classify(crop_bytes)
        return res
    except Exception as e:
        api_logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")
    finally:
        classifier_service.unload()

@router.post("/nutrition-analysis", response_model=NutritionAnalysisResponse)
def nutrition_analysis(data: NutritionAnalysisRequest, current_user: User = Depends(get_current_user)):
    try:
        analyzed_items = []
        agg = {
            "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fats": 0.0,
            "sugar": 0.0, "fiber": 0.0, "sodium": 0.0, "calcium": 0.0,
            "iron": 0.0, "vitamin_c": 0.0, "folate": 0.0
        }
        
        for item in data.items:
            fact = nutrition_service.lookup(item.name)
            # Scale nutrients based on weight (CSV values are per 100g)
            scale = item.weight_g / 100.0
            
            box = item.bounding_box
            x1 = box.x1 if box else None
            y1 = box.y1 if box else None
            x2 = box.x2 if box else None
            y2 = box.y2 if box else None
            
            item_resp = {
                "id": 0, # Placeholder, set during database insert
                "name": fact["name"],
                "display_name": nutrition_service.get_display_name(fact["name"]),
                "confidence": item.confidence,
                "nutrition_available": fact.get("nutrition_available", True),
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "weight_g": item.weight_g,
                "calories": fact["calories"] * scale,
                "protein": fact["protein"] * scale,
                "carbs": fact["carbs"] * scale,
                "fats": fact["fats"] * scale,
                "sugar": fact["sugar"] * scale,
                "fiber": fact["fiber"] * scale,
                "sodium": fact["sodium"] * scale,
                "calcium": fact["calcium"] * scale,
                "iron": fact["iron"] * scale,
                "vitamin_c": fact["vitamin_c"] * scale,
                "folate": fact["folate"] * scale
            }
            analyzed_items.append(item_resp)
            
            for k in agg.keys():
                agg[k] += item_resp[k]
                
        return {
            "items": analyzed_items,
            "aggregated": agg
        }
    except Exception as e:
        api_logger.error(f"Nutrition analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-dci", response_model=CalculateDCIResponse)
def calculate_dci(
    data: CalculateDCIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Always compute DCI for the AUTHENTICATED user — never for a
        # client-supplied user_id (prevents cross-user data inference).
        score, level = dci_service.calculate(
            data.meal_nutrition.model_dump(), current_user.id, db
        )
        return {"dci": score, "dci_level": level}
    except Exception as e:
        api_logger.error(f"DCI calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-nis", response_model=CalculateNISResponse)
def calculate_nis(data: CalculateNISRequest):
    try:
        score, level = nis_service.calculate(data.meal_nutrition.model_dump())
        return {"nis": score, "nis_level": level}
    except Exception as e:
        api_logger.error(f"NIS calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-meal", response_model=MealAnalysisResponse)
def analyze_meal(file: UploadFile = File(...), notes: str = Form(""), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    End-to-End Inference API.
    Runs the entire pipeline from food detection to disease risk fusion and stores results.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPG, JPEG, PNG, and WEBP are supported."
        )
    try:
        # 1. Save uploaded file
        unique_filename = f"{uuid.uuid4()}{ext}"
        image_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Reject corrupt / invalid images before any ML work (safe 4xx, no stack leak).
        _ensure_valid_image(image_path)

        api_logger.info(f"End-to-end analysis started for user {current_user.email}, image: {image_path}")

        # 2. YOLOv8 detection
        try:
            detections = detector_service.detect(image_path)
        finally:
            detector_service.unload()

        if not detections:
            # No YOLO food boxes: try classifying the FULL image once.
            # Accept it only if the classifier is confident; otherwise treat
            # the image as "no food recognised" so we never fabricate a food.
            try:
                from PIL import Image as PILImage
                with PILImage.open(image_path) as im:
                    fw, fh = im.size
                full_crop = crop_image(image_path, (0, 0, fw, fh))
                classification = classifier_service.classify(full_crop)
                if classification["confidence"] >= settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    detections = [{"name": "food", "confidence": 0.5, "box": (0, 0, fw, fh)}]
                    api_logger.info("No YOLO boxes; full-image classification accepted.")
                else:
                    detections = []
                    api_logger.info(
                        f"No YOLO boxes; full-image classification rejected "
                        f"(conf={classification['confidence']:.3f})."
                    )
            except Exception as e:
                api_logger.warning(f"Full-image fallback failed: {e}")
                detections = []

        # 3. Crop, Classify, & Lookup nutrition
        items_data = []
        try:
            for det in detections:
                x1, y1, x2, y2 = det["box"]
                try:
                    crop_bytes = crop_image(image_path, (x1, y1, x2, y2))
                    classification = classifier_service.classify(crop_bytes)
                    food_name = classification["class_name"]
                    conf = classification["confidence"]
                except Exception as e:
                    api_logger.error(f"Classification crop failed for box {(x1, y1, x2, y2)}. Skipping detection. Error: {e}")
                    continue

                # Confidence gating: reject low-confidence classifications so
                # non-food images / poor crops are not reported as recognised
                # foods.  Threshold documented in config.CLASSIFIER_CONFIDENCE_THRESHOLD.
                if conf < settings.CLASSIFIER_CONFIDENCE_THRESHOLD:
                    api_logger.info(
                        f"Rejected low-confidence classification '{food_name}' conf={conf:.3f}"
                    )
                    continue

                fact = nutrition_service.lookup(food_name)
                
                # Lookup the serving size
                lookup_name = food_name.lower().strip().replace(" ", "_")
                weight = DEFAULT_SERVING_WEIGHTS.get(lookup_name, 100.0)
                    
                scale = weight / 100.0
                
                display_name = nutrition_service.get_display_name(fact["name"])
                item_entry = {
                    "name": fact["name"],
                    "display_name": display_name,
                    "confidence": conf,
                    "nutrition_available": fact.get("nutrition_available", True),
                    "bounding_box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "weight_g": weight,
                    "calories": fact["calories"] * scale,
                    "protein": fact["protein"] * scale,
                    "carbs": fact["carbs"] * scale,
                    "fats": fact["fats"] * scale,
                    "sugar": fact["sugar"] * scale,
                    "fiber": fact["fiber"] * scale,
                    "sodium": fact["sodium"] * scale,
                    "calcium": fact["calcium"] * scale,
                    "iron": fact["iron"] * scale,
                    "vitamin_c": fact["vitamin_c"] * scale,
                    "folate": fact["folate"] * scale
                }
                items_data.append(item_entry)
        finally:
            classifier_service.unload()

        # If no crop passed the confidence gate, we could not confidently
        # recognise any supported food — return a friendly message instead of
        # saving a fabricated meal.
        if not items_data:
            api_logger.info(f"Analyze-meal: no confident food recognised for user {current_user.email}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="We couldn't confidently recognize a supported food in this image.",
            )

        # 4. Save Meal & Items to DB and Aggregate nutrition
        meal = meal_db_service.create_meal(current_user.id, image_path, notes, db)
        nutrition = meal_db_service.add_meal_items_and_aggregate(meal.id, items_data, db)

        # 5. DCI and NIS indices calculations
        nutrition_dict = {
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "carbs": nutrition.carbs,
            "fats": nutrition.fats,
            "sugar": nutrition.sugar,
            "fiber": nutrition.fiber,
            "sodium": nutrition.sodium,
            "calcium": nutrition.calcium,
            "iron": nutrition.iron,
            "vitamin_c": nutrition.vitamin_c,
            "folate": nutrition.folate
        }

        # Retrieve user profile demographics
        age = 30
        gender = "Male"
        height = 170.0
        weight = 70.0
        existing_conds = []

        if current_user.settings:
            age = current_user.settings.age
            gender = current_user.settings.gender
            height = current_user.settings.height
            weight = current_user.settings.weight
            existing_conds = current_user.settings.existing_conditions or []

        # Only compute indices / disease risk / fusion when at least one item
        # actually has a nutrition record.  A meal whose recognised foods all
        # lack nutrition data must NOT be silently turned into zero-nutrient
        # "perfect health" metrics.
        has_nutrition = any(it.get("nutrition_available", True) for it in items_data)

        dci = dci_level = nis = nis_level = None
        preds = None
        fusion_dict = None
        recs = []

        if has_nutrition:
            dci, dci_level = dci_service.calculate(nutrition_dict, current_user.id, db)
            nis, nis_level = nis_service.calculate(nutrition_dict)

            # 6. Disease Predictions using XGBoost
            try:
                preds = prediction_service.predict_all(
                    age, gender, height, weight, nutrition_dict, existing_conds
                )
            finally:
                prediction_service.unload()

            # 7. Risk Fusion
            fused_score, fused_level = fusion_service.fuse(
                dci, nis, preds["diabetes_risk"], preds["obesity_risk"],
                preds["hypertension_risk"], preds["deficiency_risk"]
            )
            fusion_dict = {
                "fused_score": fused_score,
                "risk_level": fused_level
            }

            # 8. ExplainDiet Recommendations
            recs = explain_diet_service.recommend(nutrition_dict, preds, dci, nis)

            # 9. Store all pipeline results to DB
            meal_db_service.save_pipeline_results(
                meal.id, dci, dci_level, nis, nis_level, preds, fusion_dict, recs, db
            )

        # 9.5 AI Dietitian (optional) — runs AFTER the meal + nutrition +
        # predictions are persisted.  Gemini is never allowed to fail the
        # meal analysis: on any error / disabled key / timeout / bad JSON,
        # ai_dietitian is simply null and the rule-based output is used.
        # Skipped entirely when no item had nutrition (nothing to analyse).
        ai_dietitian = None
        if has_nutrition and settings.GEMINI_API_KEY:
            try:
                user_profile = {
                    "age": age,
                    "gender": gender,
                    "height": height,
                    "weight": weight,
                    "existing_conditions": existing_conds,
                    "activity_level": (
                        current_user.settings.activity_level
                        if current_user.settings else None
                    ),
                }
                ai_dietitian = meal_ai_service.analyze_meal_cached(
                    db,
                    meal_id=meal.id,
                    provider=settings.LLM_PROVIDER,
                    model=settings.GEMINI_MODEL,
                    foods=items_data,
                    nutrition=nutrition_dict,
                    dci=dci,
                    dci_level=dci_level,
                    nis=nis,
                    nis_level=nis_level,
                    predictions=preds,
                    fusion=fusion_dict,
                    rule_recommendations=recs,
                    user_profile=user_profile,
                )
            except Exception as exc:
                # Never break the meal pipeline because of Gemini.
                api_logger.warning(
                    "AI Dietitian failed (%s); falling back to rule-based.",
                    type(exc).__name__,
                )
                db.rollback()
                ai_dietitian = None

        # Return complete response.  Items are built from the DB rows (real
        # ids + persisted coords) with the transient `nutrition_available`
        # flag merged from the in-memory analysis so the frontend can tell
        # the user which recognised foods have no nutrition record.
        db_items = db.query(MealItem).filter(MealItem.meal_id == meal.id).all()
        resp_items = []
        for idx, row in enumerate(db_items):
            resp_items.append({
                "id": row.id,
                "name": row.name,
                "confidence": row.confidence,
                "x1": row.x1, "y1": row.y1, "x2": row.x2, "y2": row.y2,
                "weight_g": row.weight_g,
                "calories": row.calories, "protein": row.protein, "carbs": row.carbs,
                "fats": row.fats, "sugar": row.sugar, "fiber": row.fiber,
                "sodium": row.sodium, "calcium": row.calcium, "iron": row.iron,
                "vitamin_c": row.vitamin_c, "folate": row.folate,
                "nutrition_available": items_data[idx].get("nutrition_available", True)
                if idx < len(items_data) else True,
            })

        return {
            "meal_id": meal.id,
            "image_path": f"/static/{unique_filename}", # map public URL
            "items": resp_items,
            "nutrition": nutrition,
            "dci": dci,
            "dci_level": dci_level,
            "nis": nis,
            "nis_level": nis_level,
            "predictions": preds,
            "fusion": fusion_dict,
            "recommendations": recs,
            "ai_dietitian": ai_dietitian,
            "created_at": meal.created_at
        }
        
    except HTTPException:
        # Our explicit 4xx responses (invalid image / no confident food) must
        # pass through unchanged — do not wrap them in a generic 500.
        db.rollback()
        raise
    except Exception as e:
        api_logger.error(f"End-to-end analysis error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Meal analysis failed. Please try again.",
        )
