import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.database.database import engine, Base
from backend.routes import auth, meal, prediction, user
from backend.utils.logger import app_logger

# Initialize database tables
try:
    app_logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    app_logger.info("Database tables initialized successfully.")
except Exception as e:
    app_logger.error(f"Database initialization failed: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Vision-Language-Based Food Recognition & Disease-Risk-Aware Dietary Recommendation API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware config
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "https://diet-risk-net.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static uploads directory so images are served at /static/...
# e.g. /static/some-uuid.png -> backend/uploads/some-uuid.png
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(meal.router, prefix=settings.API_V1_STR)
app.include_router(prediction.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    app_logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        app_logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        app_logger.error(f"Exception during request {request.method} {request.url.path}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred."}
        )

@app.get("/")
def read_root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "healthy",
        "message": "Welcome to the DietRiskNet FastAPI Service!"
    }
