"""Main FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import API_TITLE, API_VERSION, API_PREFIX, ALLOWED_ORIGINS
from app.database import init_db
from app.routes_crud import router as crud_router
from app.routes_dashboard import router as dashboard_router
from app.routes_reports import router as reports_router
from app.seed import seed_demo_data
from app.database import async_session
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and seed demo data on startup."""
    import sqlite3
    from app.config import DB_PATH
    
    await init_db()
    
    # Quick sync check — only seed if DB is empty
    needs_seed = True
    try:
        conn = sqlite3.connect(str(DB_PATH))
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        conn.close()
        needs_seed = count == 0
    except Exception:
        pass
    
    if needs_seed:
        async with async_session() as db:
            result = await seed_demo_data(db)
            print(f"🌱 {result['message']}")
    else:
        print("🌱 Data already seeded (skipped)")
    yield


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": API_VERSION}

# Mount API routes
app.include_router(crud_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)

@app.get("/api/historical/ratings")
def historical_ratings():
    import csv
    from pathlib import Path
    source = Path(__file__).resolve().parents[2] / "public-data" / "rating-observations.csv"
    with source.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

# Serve frontend static files (MUST be last — catches all unmatched routes)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
