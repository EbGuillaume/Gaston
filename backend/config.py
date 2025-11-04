"""Configuration management for Gaston."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class MetadataSourceConfig(BaseModel):
    """Configuration pour une source de métadonnées."""

    name: str
    enabled: bool = True
    priority: int = 1


class MetadataConfig(BaseModel):
    """Configuration des métadonnées."""

    sources: List[MetadataSourceConfig] = Field(default_factory=list)
    auto_fetch: bool = True
    auto_validate_threshold: float = 0.90
    cache_duration: Optional[int] = None
    store_covers_locally: bool = True
    covers_path: str = "/mnt/nas/.gaston/covers"


class OrganizationConfig(BaseModel):
    """Configuration de l'organisation des fichiers."""

    target_format: str = "komga"
    naming_pattern: str = "{series}/{series} {number:03d} - {title}"
    create_oneshots_folder: bool = True
    create_integrales_folder: bool = True
    separate_by_publisher: bool = False


class DeduplicationConfig(BaseModel):
    """Configuration de la déduplication."""

    enabled: bool = True
    methods: List[str] = Field(default_factory=lambda: ["hash_exact", "name_fuzzy"])
    format_priority: List[str] = Field(default_factory=lambda: ["cbz", "cbr", "epub", "pdf"])
    similarity_threshold: float = 0.85
    auto_move_duplicates: bool = True


class ScanningConfig(BaseModel):
    """Configuration du scanning."""

    max_file_size: int = 1073741824  # 1 GB
    scan_on_startup: bool = False
    file_extensions: List[str] = Field(default_factory=lambda: [".cbz", ".cbr", ".epub", ".pdf"])
    ignore_hidden: bool = True
    detect_corrupted: bool = True


class PerformanceConfig(BaseModel):
    """Configuration des performances."""

    max_workers: Optional[int] = None
    max_memory_mb: Optional[int] = None
    enable_cache: bool = True
    cache_path: str = "/tmp/.gaston/cache"


class WebConfig(BaseModel):
    """Configuration du serveur web."""

    host: str = "127.0.0.1"
    port: int = 8080
    enable_cors: bool = False
    log_level: str = "INFO"


class SpecialFoldersConfig(BaseModel):
    """Configuration des dossiers spéciaux."""

    duplicates: str = "./duplicates"
    corrupted: str = "./corrupted"
    uncategorized: str = "./_uncategorized"


class GastonConfig(BaseModel):
    """Configuration principale de Gaston."""

    version: str = "0.1.0"
    library_paths: List[str] = Field(default_factory=list)
    output_path: str = "./organized"
    special_folders: SpecialFoldersConfig = Field(default_factory=SpecialFoldersConfig)
    organization: OrganizationConfig = Field(default_factory=OrganizationConfig)
    metadata: MetadataConfig = Field(default_factory=MetadataConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    scanning: ScanningConfig = Field(default_factory=ScanningConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    web: WebConfig = Field(default_factory=WebConfig)


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "sqlite:///./gaston.db"
    database_echo: bool = False

    # Application
    app_name: str = "Gaston"
    debug: bool = False

    # Gaston configuration
    config_path: str = "./config.yaml"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[str] = None) -> GastonConfig:
    """
    Charge la configuration depuis un fichier YAML.

    Args:
        config_path: Chemin vers le fichier de configuration. Si None, utilise config.yaml

    Returns:
        Configuration Gaston validée
    """
    if config_path is None:
        config_path = os.getenv("GASTON_CONFIG", "config.yaml")

    config_file = Path(config_path)

    if not config_file.exists():
        # Retourner la configuration par défaut si le fichier n'existe pas
        return GastonConfig()

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Extraire la section 'gaston' si elle existe
    gaston_data = config_data.get("gaston", {})

    return GastonConfig(**gaston_data)


# Instance globale de configuration
settings = Settings()
gaston_config = load_config(settings.config_path)
