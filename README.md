# DietRiskNet

**Vision-Language-Based Food Recognition and Personalized Disease-Risk-Aware Dietary Recommendation Using Longitudinal Meal Analysis**

DietRiskNet is a production-ready medical-adjacent AI system that integrates computer vision models (YOLOv8 & EfficientNet) with risk-estimating models (XGBoost) and a comprehensive nutrition database to identify meal items, aggregate nutritional metrics, and predict disease hazards. It also includes a **Personalized AI Nutrition Coach** — a general conversational coach for meal planning, healthy eating, and dietary guidance that works with or without a meal analysis. The coach uses your stored meal history to show a nutrition dashboard (averages, DCI/NIS, risk trend), detect patterns (e.g. high sodium), and suggest smart goals with progress.

> **Important:** DietRiskNet produces disease-risk **estimates**, not medical
> diagnoses. Read [MODEL_LIMITATIONS.md](MODEL_LIMITATIONS.md) to understand
> what every model can and cannot tell you before interpreting any score.

---

## Technical Architecture & Flow

```mermaid
graph TD
    Upload[User Uploads Meal Image] --> YOLO[YOLOv8 detects bounding boxes]
    YOLO --> Crops[Crop detected food regions]
    Crops --> EffNet[EfficientNet classifies crops into 118 Indian dishes]
    EffNet --> CSV[Look up nutrition in Indian Food Nutrition CSV]
    CSV --> Agg[Aggregate meal macros and micronutrients]
    Agg --> DCI[Calculate Dietary Consistency Index - DCI]
    Agg --> NIS[Calculate Nutritional Imbalance Score - NIS]
    Agg & DCI & NIS --> XGB[XGBoost Predicts Diabetes, Obesity, Hypertension & Deficiency]
    XGB --> Fusion[Weighted Risk Fusion Engine]
    Fusion --> Recs[ExplainDiet Recommendation Generation]
    Recs --> Database[Save analysis record to DB]
    Database --> Dash[Update dashboard & longitudinal trends]
    Recs --> AI[AI Dietitian + Meal Chat + Nutrition Assistant]
    AI --> LLM[LLM Provider Layer: Ollama default / Gemini optional]
```

---

## Tech Stack

- **Backend:** FastAPI, Python, SQLAlchemy (PostgreSQL / SQLite fallback), Pydantic, JWT Auth, Uvicorn.
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS v4, Framer Motion, React Query, Zustand, Recharts.
- **Machine Learning:** Ultralytics YOLOv8, PyTorch (EfficientNet-B3), XGBoost, OpenCV, NumPy, Pandas.
- **LLM / AI:** provider-agnostic layer — **Ollama (default, local, no API key)** and **Gemini (optional cloud)**; ReportLab PDF.
- **Deployment:** Docker, Docker Compose.

---

## Directory Layout

```
DietRiskNet/
├── backend/
│   ├── database/        # Connection configuration and SQLAlchemy schemas
│   ├── routes/          # API endpoints routers
│   ├── schemas/         # Pydantic validation models
│   ├── services/        # Centralized business logic (Auth, ML, Nutrition, Predictions, Recs)
│   ├── trained_models/  # Core checkpoints (YOLO, EfficientNet, XGBoost, and configs)
│   ├── utils/           # Centralized logging, token auth, and PIL image utils
│   └── main.py          # App entrypoint
├── frontend/
│   ├── app/             # App Router pages (Dashboard, Log Meal, Profile, Research, etc.)
│   ├── components/      # UI Sidebar and Provider layers
│   ├── lib/             # Zustand state stores
│   └── services/        # Frontend API request handlers
├── nutrition/
│   └── indian_food_nutrition_processed.csv   # Mapped nutrition database
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites
1. **Python 3.10+** (already installed in path)
2. **Node.js LTS** (already installed in path)

### 1. Backend Service Setup (Local SQLite Fallback)
From the root project directory:
```bash
# Create virtual environment
python -m venv backend/.venv

# Activate virtual environment
# On Windows (PowerShell):
backend/.venv\Scripts\Activate.ps1
# On Linux/macOS:
source backend/.venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.main:app --reload
```
API docs will be available at `http://localhost:8000/docs` (Swagger UI).

### AI / LLM Setup (optional, for AI features)

The ML pipeline and rule-based recommendations work with **no LLM**. The AI
features (AI Dietitian, meal chat, Nutrition Assistant) use **Ollama by
default**:

```bash
ollama serve                 # start the local Ollama server
ollama pull llama3.2:3b      # pull the default model (~2 GB)
```

Optionally, set `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` in `.env` to use
Gemini as a cloud provider (with automatic fallback to Ollama). With no LLM
available, `ai_dietitian` is `null` and rule-based output is used — the app
never crashes.

### 2. Frontend Web Application Setup
From a new terminal session in the `frontend` folder:
```bash
# Install packages
npm install

# Start Next.js development server
npm run dev
```
Open `http://localhost:3000` to interact with the application.

---

## Docker Deployment (PostgreSQL Production)

To orchestrate the database, backend services, and Next.js frontend in production:
```bash
# Start all containers in the background
docker-compose up -d --build
```
- Frontend: `http://localhost:3000`
- Backend Swagger Docs: `http://localhost:8000/docs`

---

## Verification & Testing

We include a test pipeline script `backend/tests/test_pipeline.py` which loads a real sample meal image, executes the full visual crops -> class lookup -> index -> prediction -> fusion -> recommend pipeline, and checks DB insert:
```bash
# Run verification script
python -m backend.tests.test_pipeline
```
