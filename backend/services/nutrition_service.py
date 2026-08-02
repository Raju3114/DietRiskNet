import csv
import os
import difflib
from backend.config import settings
from backend.utils.logger import app_logger

# Pre-defined Synonym / Alias map for mapping the 360 classifier outputs to the 1015 CSV dishes
SYNONYM_MAP = {
    # Classifier outputs -> CSV dishes
    "butter_naan": "Naan",
    "chapati": "Chapati/Roti",
    "chai": "Hot tea (Garam Chai)",
    "chole_bhature": "Chickpeas curry (Safed channa curry)",
    "dal_makhani": "Dal makhani",
    "dhokla": "Dhokla",
    "idli": "Idli",
    "jalebi": "Gulab Jamun with khoya",
    "kaathi_rolls": "Paneer kaathi roll",
    "kadai_paneer": "Pea paneer curry (Matar paneer)",
    "kulfi": "Kulfi",
    "masala_dosa": "Masala dosa",
    "momos": "Spring roll",
    "paani_puri": "Bhel puri",
    "pakode": "Mixed vegetable pakora/pakoda",
    "pav_bhaji": "Pav bhaji",
    "samosa": "Vegetable samosa",
    "rice": "Boiled rice (Uble chawal)",
    "apple": "Fruit salad (Phalon ka salaad)",
    "banana": "Fruit salad (Phalon ka salaad)",
    "carrot": "Carrot and cabbage with coconut (Nariyal ke saath pattagobhi aur gajar)",
    "cucumber": "Cucumber and yogurt salad (Kheere aur dahi ka salad)",
    "potato": "Potato cauliflower (Aloo gobhi)",
    "tomato": "Clear tomato soup (Tamatar ka soup)",
    "pizza": "Cheese pizza",
    "burger": "Vegetable burger",
    "french_fries": "Dry potato (Sookhe aloo)",
    "fried_rice": "Chinese fried rice",
    "spring_rolls": "Spring roll",
    "chicken_curry": "Chicken curry",
    "caesar_salad": "Tossed green salad",
    "garlic_bread": "Cheese toast",
    "ice_cream": "Vanilla ice cream without egg",
    "miso_soup": "Clear tomato soup (Tamatar ka soup)",
    "waffles": "Pancake",
    "donuts": "Sponge cake",
    "doughnut": "Sponge cake",
    "macarons": "Chickpea flour cookies (Sweet besan rounds/cookies)",
    "tacos": "Paneer kaathi roll",
    "tiramisu": "Chocolate cake",
    "cheesecake": "Plain cream cake",
    # Additional B3 Model mappings (nutritionally similar equivalents)
    "apple_pie": "Apple cinnamon pie",
    "bread_pudding": "Bread and butter pudding",
    "breakfast_burrito": "Stuffed egg omelette/omlet",
    "caprese_salad": "Tossed salad",
    "carrot_cake": "Carrot cake (Gajar ka cake)",
    "crab_cakes": "Fish cutlet (Machli ka cutlet)",
    "creme_brulee": "Caramel custard (steamed)",
    "cup_cakes": "Plain cream cake",
    "dumplings": "Spring roll",
    "eggs_benedict": "Egg sandwich (Ande ka sandwich)",
    "falafel": "Spinach chickpeas cutlet (Palak channa dal cutlet)",
    "fish_and_chips": "Fried fish and Chips (English Style) (Tali hui machli aur chips)",
    "french_toast": "French omelette/omlet",
    "greek_salad": "Tossed green salad",
    "grilled_cheese_sandwich": "Cheese toast",
    "grilled_salmon": "Tandoori fish",
    "gyoza": "Spring roll",
    "hamburger": "Vegetable burger",
    "huevos_rancheros": "Stuffed egg omelette/omlet",
    "lasagna": "Macroni cheese pie",
    "omelette": "Plain omelette/omlet",
    "onion_rings": "Onion pakora/pakoda (Pyaaz ke pakode)",
    "paella": "Spanish rice",
    "panna_cotta": "Caramel custard (steamed)",
    "peking_duck": "Roast chicken",
    "pho": "Chicken consomme (Clear chicken soup)",
    "ramen": "Chicken consomme (Clear chicken soup)",
    "ravioli": "Macroni cheese pie",
    "red_velvet_cake": "Chocolate cake",
    "seaweed_salad": "Tossed green salad",
    "spaghetti_carbonara": "Macroni cheese pie",
    "strawberry_shortcake": "Plain cream cake",
    # Additional defensible mappings (validated against the CSV during audit).
    # Only classes with a genuinely similar existing Indian record were added;
    # classes with no defensible equivalent remain unresolved and are surfaced
    # to the UI as nutrition-unavailable (see lookup()).
    "hummus": "Chickpeas curry (Safed channa curry)",                       # chickpea-based dip vs chickpea curry
    "edamame": "Soyabean curry",                                            # young soy beans vs soy curry
    "frozen_yogurt": "Vanilla ice cream without egg",                       # dairy frozen dessert
    "risotto": "Boiled rice (Uble chawal)",                                 # rice-based dish
    "gnocchi": "Potato parantha/paratha (Aloo ka parantha/paratha)",        # potato-based
    "croque_madame": "Egg sandwich (Ande ka sandwich)",                     # bread + egg + cheese
    "pad_thai": "Home made plain noodles",                                  # noodle dish
    "fried_calamari": "Fried fish (Indian style) (Tali hui machli)",        # fried seafood
    "shrimp_and_grits": "Prawn curry (with coconut) (Jhinga curry)",        # shellfish
    "bruschetta": "Cheese and tomato sandwich (toasted) (Cheese aur tamatar ke sandwich (toasted))",  # toasted bread + tomato
}

# Display-name overrides for the frontend.
#
# These are applied when the CSV dish name contains a default modifier
# (e.g. "Vegetable samosa") that can be omitted for a cleaner display
# without changing the meaning of the dish.
#
# Only entries where the modifier is truly redundant are listed here.
# Dishes where removing the modifier would change the identity
# (e.g. "Chicken biryani" vs "Vegetable biryani", "Masala dosa" vs
# "Plain dosa") are intentionally NOT included.
DISPLAY_NAMES = {
    # Samosa — "vegetable" is the default, no other variety exists in the DB
    "Vegetable samosa": "Samosa",
    # Dosa varieties — "plain" is redundant, other varieties have their own names
    "Plain dosa": "Dosa",
    # Idli — same reasoning
    "Plain idli": "Idli",
    # Omelette — "plain" is redundant
    "Plain omelette/omlet": "Omelette",
    # Burger — "vegetable" is the default in this database
    "Vegetable burger": "Burger",
    # Cutlet — "vegetable" is the default
    "Vegetable cutlet": "Cutlet",
    # Roll — "vegetable" is the default
    "Vegetable roll": "Roll",
}


class NutritionService:
    def __init__(self):
        self.nutrition_db = {}
        self.normalized_db = {}
        self.load_nutrition_db()

    def load_nutrition_db(self):
        csv_path = settings.NUTRITION_CSV_PATH
        if not os.path.exists(csv_path):
            app_logger.error(f"Nutrition CSV not found at {csv_path}")
            return
        
        try:
            app_logger.info(f"Loading nutrition database from {csv_path}")
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dish_name = row.get("Dish Name", "").strip()
                    if not dish_name:
                        continue
                    
                    # Parse nutritional facts
                    data = {
                        "name": dish_name,
                        "nutrition_available": True,
                        "calories": float(row.get("Calories (kcal)", 0) or 0),
                        "carbs": float(row.get("Carbohydrates (g)", 0) or 0),
                        "protein": float(row.get("Protein (g)", 0) or 0),
                        "fats": float(row.get("Fats (g)", 0) or 0),
                        "sugar": float(row.get("Free Sugar (g)", 0) or 0),
                        "fiber": float(row.get("Fibre (g)", 0) or 0),
                        "sodium": float(row.get("Sodium (mg)", 0) or 0),
                        "calcium": float(row.get("Calcium (mg)", 0) or 0),
                        "iron": float(row.get("Iron (mg)", 0) or 0),
                        "vitamin_c": float(row.get("Vitamin C (mg)", 0) or 0),
                        "folate": float(row.get("Folate (µg)", 0) or 0),
                    }
                    
                    self.nutrition_db[dish_name] = data
                    self.normalized_db[self._normalize_name(dish_name)] = data
                    
            app_logger.info(f"Loaded {len(self.nutrition_db)} dishes into nutrition lookup.")
        except Exception as e:
            app_logger.error(f"Failed to load nutrition CSV: {e}")

    def _normalize_name(self, name: str) -> str:
        """
        Applies deterministic normalization:
        Lowercases, strips, replaces underscores/dashes/special symbols with space.
        """
        if not name:
            return ""
        name = name.lower().strip()
        name = name.replace("_", " ").replace("-", " ")
        # Remove multiple spaces
        return " ".join(name.split())

    def lookup(self, food_name: str) -> dict:
        """
        Looks up nutrition by following priority:
        Priority 1: Exact food name match in original database.
        Priority 2: Alias / Synonym map lookup.
        Priority 3: Deterministic normalization search.
        Priority 4: Fuzzy matching fallback.
        """
        if not food_name:
            return self._default_nutrition("Unknown")

        # Priority 1: Exact Match
        if food_name in self.nutrition_db:
            app_logger.info(f"Nutrition lookup Success (Priority 1 - Exact): {food_name}")
            return self.nutrition_db[food_name]

        # Priority 2: Alias/Synonym mapping
        mapped_name = SYNONYM_MAP.get(food_name)
        if mapped_name and mapped_name in self.nutrition_db:
            app_logger.info(f"Nutrition lookup Success (Priority 2 - Alias): {food_name} -> {mapped_name}")
            return self.nutrition_db[mapped_name]

        # Priority 3: Deterministic normalization
        norm_name = self._normalize_name(food_name)
        if norm_name in self.normalized_db:
            matched_dish = self.normalized_db[norm_name]
            app_logger.info(f"Nutrition lookup Success (Priority 3 - Normalization): {food_name} -> {matched_dish['name']}")
            return matched_dish

        # Priority 4: Fuzzy matching fallback
        norm_keys = list(self.normalized_db.keys())
        matches = difflib.get_close_matches(norm_name, norm_keys, n=1, cutoff=0.75)
        if matches:
            matched_dish = self.normalized_db[matches[0]]
            app_logger.info(f"Nutrition lookup Success (Priority 4 - Fuzzy): {food_name} -> {matched_dish['name']}")
            return matched_dish

        # Unmatched log
        app_logger.warning(f"Nutrition lookup failed for food: '{food_name}'. Returning default values.")
        return self._default_nutrition(food_name)

    def get_display_name(self, dish_name: str) -> str | None:
        """Return a friendlier display label for *dish_name*, or ``None``.

        The original CSV dish name is always returned in the ``name``
        field so that the raw data is preserved.  This method produces
        an optional ``display_name`` that the frontend can render in
        place of the raw name.

        To add a new display label, add an entry to ``DISPLAY_NAMES``.
        """
        return DISPLAY_NAMES.get(dish_name)

    def _default_nutrition(self, name: str) -> dict:
        return {
            "name": f"Unresolved: {name}" if name != "Unknown" else "Unknown",
            "nutrition_available": False,  # no valid record — must not be treated as real zeros
            "calories": 0.0,
            "carbs": 0.0,
            "protein": 0.0,
            "fats": 0.0,
            "sugar": 0.0,
            "fiber": 0.0,
            "sodium": 0.0,
            "calcium": 0.0,
            "iron": 0.0,
            "vitamin_c": 0.0,
            "folate": 0.0
        }

# Singleton instance of NutritionService
nutrition_service = NutritionService()
