"""Metadata scrapers."""
from backend.scrapers.base import BaseScraper, MetadataResult
from backend.scrapers.bedetheque import BedethequeScraper
from backend.scrapers.bdphile import BDPhileScraper

__all__ = ["BaseScraper", "MetadataResult", "BedethequeScraper", "BDPhileScraper"]
