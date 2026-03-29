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


def _parse_csv_env(value: str | None) -> list[str]:
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


frontend_origins = _parse_csv_env(
    os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
)

# Cookie/session auth requires credentials, but bearer-token-only auth should keep this off.
allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", default=False)
if allow_credentials and not frontend_origins:
    # Credentials + wildcard/empty origins is blocked by browsers; disable credentials if misconfigured.
    allow_credentials = False

app = FastAPI(
    title="QuickApply.AI",
    description="AI-powered college application platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=allow_credentials,
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


@app.get("/dev/token")
async def dev_token():
    """DEVELOPMENT ONLY - remove before production"""
    from jose import jwt
    from datetime import datetime, timedelta
    payload = {
        "sub": "29cf3a20-8688-431a-b5f0-2a5a43a20976",  # your test user ID
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    token = jwt.encode(payload, os.getenv("SECRET_KEY", "changeme"), algorithm="HS256")
    return {"token": token, "note": "DEV ONLY - 30 day token"}
