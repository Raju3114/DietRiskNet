import pandas as pd
import numpy as np

csv_path = r"d:\DietRiskNet\nutrition\indian_food_nutrition_processed.csv"
df = pd.read_csv(csv_path)

# 1. Fill missing Vitamin C and Folate with 0.0
# The columns are 'Vitamin C (mg)' and 'Folate (µg)'
folate_col = [c for c in df.columns if 'Folate' in c][0]

df['Vitamin C (mg)'] = df['Vitamin C (mg)'].fillna(0.0)
df[folate_col] = df[folate_col].fillna(0.0)

# 2. Correct the 23 soups/sauces that have huge caloric inconsistencies
# We will define the target lists and updates
soup_corrections = {
    "Lentil soup": {"fat": 1.2, "protein": 2.5},
    "Chicken consomme (Clear chicken soup)": {"fat": 1.0, "protein": 3.0},
    "Chicken sweet corn soup": {"fat": 1.5, "protein": 2.5},
    "Minestrone soup": {"fat": 1.0, "protein": 1.8},
    "Egg drop soup": {"fat": 1.5, "protein": 2.2},
    "French onion soup": {"fat": 2.0, "protein": 1.5},
    "Talaumein soup": {"fat": 1.5, "protein": 2.0},
    "Cold summer garden soup": {"fat": 1.5, "protein": 1.8},
    "Meat consomme (with mutton)": {"fat": 1.2, "protein": 3.5},
    "Consomme au julienne": {"fat": 1.0, "protein": 2.0},
    "Consomme au vermicelli": {"fat": 1.0, "protein": 2.2},
    "Green pea soup (Matar ka soup)": {"fat": 1.2, "protein": 2.5},
    "Spinach soup (Palak ka soup)": {"fat": 1.2, "protein": 2.2},
    "Mixed vegetable soup": {"fat": 1.0, "protein": 1.5},
    "Cheese soup": {"fat": 5.0, "protein": 3.0},
    "Mulligatawny soup": {"fat": 2.0, "protein": 2.2},
    "Cream of carrot soup": {"fat": 3.0, "protein": 1.5},
    "Cream of broccoli soup": {"fat": 3.0, "protein": 1.8},
    "Cream of potato soup": {"fat": 3.0, "protein": 1.5},
    "Almond soup (Badam ka soup)": {"fat": 4.5, "protein": 2.0},
    "Millet soup": {"fat": 1.5, "protein": 2.2},
    "Classic seasoned black beans": {"fat": 1.0, "protein": 4.0},
    "Brown sauce": {"fat": 4.0, "protein": 1.0}
}

for dish, updates in soup_corrections.items():
    idx = df[df['Dish Name'] == dish].index
    if len(idx) > 0:
        df.loc[idx, 'Fats (g)'] = updates['fat']
        df.loc[idx, 'Protein (g)'] = updates['protein']
        # Recalculate Calories
        carbs = df.loc[idx, 'Carbohydrates (g)'].values[0]
        cal = carbs * 4 + updates['protein'] * 4 + updates['fat'] * 9
        df.loc[idx, 'Calories (kcal)'] = round(cal, 2)
        print(f"Corrected '{dish}': Carbs={carbs}g, Prot={updates['protein']}g, Fat={updates['fat']}g -> Cal={round(cal, 2)} kcal")

# Save cleaned CSV
df.to_csv(csv_path, index=False)
print("Cleaned CSV database saved successfully.")
