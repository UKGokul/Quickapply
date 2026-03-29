from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from routes.applications import router as applications_router
from routes.documents import router as documents_router
import os

load_dotenv()

app = FastAPI(
    title="QuickApply.AI",
    description="AI-powered college application platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ Database initialized")

# Register routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(documents_router)
app.include_router(applications_router)

@app.get("/")
def root():
    return {"status": "QuickApply.AI backend is running"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "ai_provider": os.getenv("AI_PROVIDER", "not set"),
        "database": os.getenv("DATABASE_URL", "not set")
    }
