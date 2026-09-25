"""Endpoints and constants for Lantmäteriet's raster STAC services."""

from __future__ import annotations

from dataclasses import dataclass

PLUGIN_NAME = "LM-STAC Downloader"
SETTINGS_PREFIX = "lm_stac_downloader"

API_URL = "https://api.lantmateriet.se"
TOKEN_URL = "https://apimanager.lantmateriet.se/oauth2/token"

# The API takes the WGS 84 bbox/intersects of plain STAC.
SEARCH_CRS = "EPSG:4326"
PAGE_LIMIT = 100
MAX_RESULTS = 1000
# Ask for confirmation before downloading more than this.
WARN_BYTES = 2 * 1024**3


@dataclass(frozen=True)
class Service:
    key: str
    label: str
    path: str
    has_years: bool


SERVICES = {
    "ortofoto": Service("ortofoto", "Ortofoto", "/stac-bild/v1", True),
    "hojd": Service("hojd", "Höjddata (markhöjdmodell)", "/stac-hojd/v1", False),
}
DEFAULT_SERVICE = "ortofoto"


def search_base_url(service_key: str) -> str:
    return API_URL + SERVICES[service_key].path
