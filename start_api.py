# start_api.py
from asyncio.streams import start_unix_server
import uvicorn
from api.main import app
from tkr_utils.config_logging import setup_logging

logger = setup_logging(__file__)

if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
