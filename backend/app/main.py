# backend/app/main.py
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.db.database import init_db, get_db
from app.api import health, hello, compliance, rule_sets, admin  # Import API modules
from app.db.migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# Add CORS middleware to handle CORS at the application level
# This ensures CORS headers are properly set even if Traefik doesn't handle them
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://legal-colliers.dev.morphing.ai", "http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured for legal-colliers.dev.morphing.ai")

# Get API prefix from settings and normalize it
raw_prefix = settings.API_PREFIX.strip()

# Special case: if the path is just "/", use empty string for FastAPI
if raw_prefix == "/":
    api_prefix = ""
    logger.info("Using root path (empty prefix)")
else:
    # Otherwise normalize the prefix
    # Ensure it starts with a slash
    if not raw_prefix.startswith('/'):
        raw_prefix = '/' + raw_prefix
        
    # Remove trailing slash if present
    if raw_prefix.endswith('/'):
        raw_prefix = raw_prefix[:-1]
        
    api_prefix = raw_prefix
    logger.info(f"Using API prefix: '{api_prefix}'")

# Include routers with the normalized API prefix
app.include_router(health.router, prefix=api_prefix, tags=["health"])
app.include_router(hello.router, prefix=api_prefix, tags=["hello"])
app.include_router(compliance.router, prefix=f"{api_prefix}/compliance", tags=["compliance"])
app.include_router(rule_sets.router, prefix=f"{api_prefix}/rules", tags=["rule_sets"])
app.include_router(admin.router, prefix=f"{api_prefix}", tags=["admin"])

# Add a global exception handler to log unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"detail": "Internal server error"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully.")
    
    # Run migrations
    logger.info("Running database migrations...")
    from app.db.database import async_session_factory
    async with async_session_factory() as db:
        await run_migrations(db)
    logger.info("Migrations completed.")
    
    logger.info(f"Application running in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)