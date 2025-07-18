from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.database import init_database, close_database
from app.api.routes import auth, stocks, chat, websocket
from app.services.price_updater import price_updater

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()
    print("Database initialized")
    
    # Start background price updater
    await price_updater.start()
    print("Price updater started")
    
    yield
    
    # Shutdown
    await price_updater.stop()
    print("Price updater stopped")
    
    await close_database()
    print("Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Conversational Stock Analysis Platform Backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["Stocks"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/api/v1/ws"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "environment": settings.ENVIRONMENT,
        "features": {
            "auth": True,
            "stocks": True,
            "chat": True,
            "websocket": True,
            "real_time_updates": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.DEBUG else False,
        log_level="info"
    )