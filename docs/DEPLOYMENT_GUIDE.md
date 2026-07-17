# DietRiskNet Production Deployment Guide

This document describes the steps required to prepare, build, and deploy the **DietRiskNet** platform to production environments.

---

## 1. Production Architecture Overview

DietRiskNet is designed as a decoupled architecture:
* **Frontend**: Next.js single-page application (SPA), ideal for static web hosting or edge rendering.
* **Backend**: FastAPI (Python) service that handles compute-heavy processes (ML inference, DB logic).
* **Database**: PostgreSQL (Production) or SQLite (Development).
* **Storage**: Persistent storage bucket/directory for uploaded meal photos and ML model files.

---

## 2. Environment Variables Specification

Ensure these variables are configured in your cloud hosting provider dashboards:

### Backend Production Environment Variables
| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `SECRET_KEY` | JWT signing security key | `generate-a-secure-random-string-for-production` |
| `MODELS_DIR` | Directory containing model weights | `/app/backend/trained_models` |
| `NUTRITION_CSV_PATH` | Path to nutrition lookup CSV | `/app/nutrition/indian_food_nutrition_processed.csv` |
| `UPLOAD_DIR` | Directory for meal upload images | `/app/backend/uploads` |

### Frontend Production Environment Variables
| Variable | Description | Example Value |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Public URL of the running FastAPI server | `https://api.dietrisknet.org/api` |

---

## 3. Backend Deployment (e.g., Render, Railway, or AWS ECS)

The backend runs heavy ML model weights (YOLOv8 + EfficientNet + XGBoost), requiring specific settings:

### A. Compute Resource Requirements
* **RAM**: At least **2GB RAM** (4GB recommended) is required to load PyTorch, torchvision, YOLO, and classifier weights into memory on startup.
* **Storage**: Ensure you mount a persistent volume at `/app/backend/uploads` so uploaded meal photos are not lost when container builds recycle.

### B. Command Configuration
Set the start command to:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
If using a custom Docker deployment, reference `./backend/Dockerfile`.

### C. Large File Storage (LFS)
Since ML model weight files (such as `.pt` and `.pth`) exceed typical Git limits, ensure you download or configure them securely. If deploying via container registry (Docker Hub / AWS ECR), package these files directly inside the image or mount them from an S3 bucket or GCP volume during deployment.

---

## 4. Frontend Deployment (e.g., Vercel or Netlify)

Vercel is the recommended platform for hosting the Next.js frontend.

### A. Next.js Static Optimization
During build time, Next.js will verify TypeScript and compile the app.
* Set **Build Command**: `npm run build`
* Set **Output Directory**: `.next` or `out` (depending on export settings)
* Set **Environment Variable**: `NEXT_PUBLIC_API_URL` pointing to the public backend endpoint.

### B. Routing Fallbacks
Since this is a client-side routing application, configure rewrites in Vercel to route all pages to `index.html` if using static exports. If deploying as a standard Next.js app, routing fallbacks are handled automatically by the Next.js runtime.

---

## 5. PostgreSQL Database Configuration

In production, SQLite is not suitable due to concurrency constraints and lack of persistence across server restarts.
1. Provision a PostgreSQL instance (e.g. AWS RDS, GCP Cloud SQL, or Neon).
2. Set the `DATABASE_URL` env variable in the backend to the postgres string: `postgresql://<user>:<password>@<host>:<port>/<dbname>`.
3. The SQLAlchemy initialization script in `backend/main.py` is fully compatible with PostgreSQL and will create all tables (`User`, `UserSetting`, `Meal`, `MealItem`, `MealNutrition`, etc.) automatically upon the first connection.

---

## 6. Docker Container Orchestration

To deploy DietRiskNet to container hosts (e.g., AWS ECS, GCP Cloud Run, or DigitalOcean App Platform):

1. **Build and push Backend Image**:
   ```bash
   docker build -t registry.example.com/dietrisknet-backend:latest -f ./backend/Dockerfile .
   docker push registry.example.com/dietrisknet-backend:latest
   ```
2. **Build and push Frontend Image**:
   ```bash
   docker build -t registry.example.com/dietrisknet-frontend:latest -f ./frontend/Dockerfile ./frontend
   docker push registry.example.com/dietrisknet-frontend:latest
   ```
3. Deploy the containers, passing the appropriate environment variables. Ensure the backend container has a persistent volume attached at `/app/backend/uploads` for patient meal scan files.

---

## 7. Common Deployment Issues & Resolutions

### A. Render Service Request Timeout
* **Issue**: The Render service times out during deployment.
* **Cause**: On startup, PyTorch loads YOLO and classifier weights which can take up to 45 seconds on low-cpu plans.
* **Fix**: Increase the healthcheck timeout threshold or allocate a minimum of 2 dedicated CPUs.

### B. Vercel Serverless Function Timeout (CORS / Uploads)
* **Issue**: File uploads time out.
* **Cause**: Next.js client attempts to upload files directly but is capped by edge execution time limits (10s on hobby plans).
* **Fix**: Ensure the frontend uploads directly to the FastAPI backend server (which has no strict execution limit) rather than using Vercel serverless proxy API routes.

### C. CORS Blocked
* **Issue**: Requests from frontend fail with `CORS policy` warnings.
* **Cause**: The backend allows origins, but if you have strict proxy settings, it might block the domain.
* **Fix**: In `backend/main.py`, verify `allow_origins=["*"]` allows the deployed frontend domain explicitly (e.g. `allow_origins=["https://dietrisknet.vercel.app"]`).
