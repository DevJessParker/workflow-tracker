"""
Pinata Code - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# Import routers
from app.routers import scanner

# Create FastAPI app
app = FastAPI(
    title="Pinata Code API",
    description="Backend API for Pinata Code - Code Workflow Analysis SaaS Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scanner.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🪅 Pinata Code API",
        "tagline": "It's what's inside that counts",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "service": "pinata-backend",
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "authentication": "planned",
            "organizations": "planned",
            "repositories": "planned",
            "scans": "planned",
            "billing": "planned",
        },
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🪅 Pinata Code Backend starting...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS origins: {CORS_ORIGINS}")
    print("✅ Backend ready!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("🛑 Pinata Code Backend shutting down...")
