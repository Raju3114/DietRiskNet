# DietRiskNet Setup & Execution Guide

This document outlines the detailed instructions to set up, configure, run, and test **DietRiskNet** in your local development environment.

---

## 1. Project Overview

**DietRiskNet** is a Vision-Language-Based Food Recognition and Personalized Disease-Risk-Aware Dietary Recommendation platform. It integrates:
* **YOLOv8** object detector for localizing food items.
* **EfficientNet-B0** classifier for categorizing 360 unique food items.
* An Indian food nutrition database mapping to estimate portion-specific calories and macronutrients.
* Four clinical **XGBoost** diagnostic classifiers for predicting Diabetes, Obesity, Hypertension, and Nutritional Deficiency risks.
* An **ExplainDiet** recommendation engine providing personalized clinical advice based on daily logs.

---

## 2. Prerequisites

Ensure you have the following system dependencies installed:
* **Python**: `3.10.x` (Recommended) or `3.11.x`
* **Node.js**: `v20.x` (LTS) or higher
* **NPM**: `v10.x` or higher
* **Git**: Installed and configured (for cloning and tracking)
* **Docker** & **Docker Compose**: Required if running containerized environments

---

## 3. Backend Setup (FastAPI)

Follow these steps to initialize the Python backend server:

### A. Create a Virtual Environment
Navigate to the root directory and create a virtual environment:
```bash
# Windows (PowerShell/CMD)
python -m venv backend/.venv

# macOS / Linux
python3 -m venv backend/.venv
```

### B. Activate the Virtual Environment
Activate the environment to sandbox your dependencies:
```powershell
# Windows (PowerShell)
.\backend\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\backend\.venv\Scripts\activate.bat

# macOS / Linux
source backend/.venv/bin/activate
```

### C. Install Dependencies
Ensure you install the required packages inside the virtual environment:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### D. Environment Variables Configuration
Copy the sample environment file to `.env` in the root:
```bash
cp .env.example .env
```
Inside `.env`, verify the following configurations:
```env
DATABASE_URL=sqlite:///./dietrisknet.db
SECRET_KEY=dietrisknet_super_secret_jwt_key_2026_capstone
MODELS_DIR=d:\DietRiskNet\backend\trained_models
NUTRITION_CSV_PATH=d:\DietRiskNet\nutrition\indian_food_nutrition_processed.csv
UPLOAD_DIR=d:\DietRiskNet\backend\uploads
```
*Note: Ensure all paths point correctly to your local directories.*

### E. Initialize Database & Run Backend
Start the backend FastAPI server using `uvicorn`:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Upon startup, the database tables will automatically initialize in `dietrisknet.db`.
You can verify the backend is running by opening:
* API Health Check: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 4. Frontend Setup (Next.js)

Follow these steps to initialize the Next.js React frontend application:

### A. Navigate to the Frontend Folder
```bash
cd frontend
```

### B. Install Node.js Packages
```bash
npm install
```

### C. Configure Local Environment Variables
Create a file named `.env.local` inside the `frontend` folder:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### D. Start Next.js Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser. The application should immediately load the clinical landing page.

---

## 5. Running Verification Tests

To verify that the entire ML model pipeline, databases, and calculation matrices function correctly, run the integration test suite:

```bash
# Ensure your virtual environment is active
.\backend\.venv\Scripts\python.exe backend/tests/test_pipeline.py
```
This script executes:
1. SQLite test database seeding.
2. Loading of YOLO, EfficientNet, and XGBoost models.
3. Food item detection, crop segmentation, classification, and RDI mapping.
4. Consistency index computations (DCI, NIS).
5. Comprehensive fusion assessment and recommendation generation.
6. DB assertion checks.

---

## 6. Production Compilation

### A. Next.js Production Build
To test frontend production builds, run:
```bash
cd frontend
npm run build
npm run start
```
This checks TypeScript typing safety and compiles statically optimized pages.

---

## 7. Docker Containerization

To run the entire suite (PostgreSQL, FastAPI, Next.js) using Docker:

```bash
# Build and spin up the containers
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d --build

# Stop the containers
docker-compose down
```
When running via Docker Compose:
* **Frontend**: Accessible at [http://localhost:3000](http://localhost:3000)
* **Backend**: Accessible at [http://localhost:8000](http://localhost:8000)
* **Database (PostgreSQL)**: Accessible at port `5432`

---

## 8. Troubleshooting & Common Fixes

### A. Model Weights Missing
If you see the error:
`FileNotFoundError: [Errno 2] No such file or directory...`
Ensure the files in `backend/trained_models` exist:
* `DietRiskNet_FoodDetector_YOLOv8.pt`
* `DietRiskNet_FoodClassifier_EfficientNetB0.pth` (or `DietRiskNet_FoodClassifier_EfficientNetB3.pth`)
* `DietRiskNet_Diabetes_XGBoost.pkl`
* `DietRiskNet_Obesity_XGBoost.pkl`
* `DietRiskNet_Hypertension_XGBoost.pkl`
* `DietRiskNet_NutritionalDeficiency_XGBoost.pkl`

### B. Address Already in Use (Port 8000 or 3000)
If the port is occupied:
* Find the process ID: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (macOS/Linux)
* Terminate the process: `taskkill /PID <PID> /F` (Windows) or `kill -9 <PID>` (macOS/Linux)
* Alternatively, change the port flag on startup: `uvicorn backend.main:app --port 8080`

### C. CORS Errors on Uploads
If the browser blocks requests to the backend:
* Verify that `CORSMiddleware` in `backend/main.py` allows the origin. Under local development, the origins are configured to allow `*`.

### D. PyTorch CPU vs CUDA Warnings
If uvicorn shows warnings about CUDA missing:
* This is expected in environments without GPUs. The backend is configured to fall back gracefully to `cpu`.
