"""
Pinata Code - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import redis.asyncio as aioredis

# Import API routes
from app.api.scanner import router as scanner_router

# Import routers
from app.routers import scanner, scanner_websocket

# Create FastAPI app
app = FastAPI(
    title="Pinata Code API",
    description="Backend API for Pinata Code - Code Workflow Analysis SaaS Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API routers
app.include_router(scanner_router)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors for debugging"""
    print(f"❌ Validation error on {request.method} {request.url.path}")
    print(f"❌ Error details: {exc.errors()}")
    try:
        body = await request.body()
        print(f"❌ Request body: {body.decode('utf-8')}")
    except:
        print(f"❌ Could not read request body")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
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
app.include_router(scanner_websocket.router)


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
    from app.redis_client import check_redis_connection, get_redis_info

    print("🪅 Pinata Code Backend starting...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS origins: {CORS_ORIGINS}")

    # Check Redis connection
    if check_redis_connection():
        info = get_redis_info()
        print(f"📡 Redis: Connected ({info.get('version', 'unknown')} - {info.get('connected_clients', 0)} clients)")
    else:
        print("⚠️  Redis: Connection failed - WebSocket updates will not work")

    print("✅ Backend ready!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("🛑 Pinata Code Backend shutting down...")

    # Close Redis connection
    from app.api.scanner import redis_client
    if redis_client:
        await redis_client.close()
        print("📡 Redis: Connection closed")
