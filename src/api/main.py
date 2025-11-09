"""FastAPI application setup and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .middleware import LocalhostOnlyMiddleware

app = FastAPI(
    title="AI Chat API",
    description="REST API for AI Chat Web Interface",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add localhost-only security middleware
app.add_middleware(LocalhostOnlyMiddleware)

# Configure CORS for localhost origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("AI Chat API starting...")
    print("API Documentation: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("AI Chat API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
