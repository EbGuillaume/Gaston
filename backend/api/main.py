"""Main FastAPI application."""
import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import gaston_config, settings
from backend.database.session import init_db

# Création de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Smart library organizer for books, comics, manga, and BDs",
    version=gaston_config.version,
    debug=settings.debug,
)

# Configuration CORS
if gaston_config.web.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Actions à effectuer au démarrage de l'application."""
    logger.info(f"Starting {settings.app_name} v{gaston_config.version}")
    logger.info(f"Database URL: {settings.database_url}")

    # Initialisation de la base de données
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à effectuer à l'arrêt de l'application."""
    logger.info(f"Shutting down {settings.app_name}")


@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "name": settings.app_name,
        "version": gaston_config.version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# CLI pour lancer l'application
@click.group()
def cli():
    """Gaston - Smart library organizer."""
    pass


@cli.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def start(host: str, port: int, reload: bool):
    """Start the Gaston web server."""
    host = host or gaston_config.web.host
    port = port or gaston_config.web.port

    logger.info(f"Starting Gaston on {host}:{port}")

    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=gaston_config.web.log_level.lower(),
    )


@cli.command()
def init():
    """Initialize the database."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully!")


@cli.command()
def dev():
    """Start the development server with auto-reload."""
    host = gaston_config.web.host
    port = gaston_config.web.port

    logger.info(f"Starting Gaston in DEV mode on {host}:{port}")

    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    cli()
