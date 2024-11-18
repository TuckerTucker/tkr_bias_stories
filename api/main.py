# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stories
from tkr_utils.config_logging import setup_logging

logger = setup_logging(__file__)

app = FastAPI(title="Bias Stories API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stories.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Bias Stories API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
