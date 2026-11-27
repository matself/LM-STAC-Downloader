"""Endpoints and constants for Lantmäteriet's STAC services (rasters and point clouds)."""

from __future__ import annotations

from dataclasses import dataclass

PLUGIN_NAME = "Geodata: Ortofoto & höjd (Lantmäteriet)"
SETTINGS_PREFIX = "lm_stac_downloader"

API_URL = "https://api.lantmateriet.se"
TOKEN_URL = "https://apimanager.lantmateriet.se/oauth2/token"  # nosec B105 - public endpoint URL, not a secret

# The API takes the WGS 84 bbox/intersects of plain STAC.
SEARCH_CRS = "EPSG:4326"
PAGE_LIMIT = 1000
# A search with more hits than this is given up: no hits are kept.
MAX_RESULTS = 10000
# The list and the map outlines stay empty while the filtered hits are more than this.
MAX_SHOWN = 1000
# Ask for confirmation before downloading more than this.
WARN_BYTES = 2 * 1024**3


@dataclass(frozen=True)
class Service:
    key: str
    label: str
    path: str
    has_years: bool
    # Restrict the search to this collection (needed for point clouds, which share
    # /stac-hojd/v1 with the elevation rasters).
    collection: str | None = None
    point_cloud: bool = False
    # Paid collections (not `dsm-skoglig-copc`, which is free): the plugin only fetches free data. The catalogue lists them, but the
    # download server refuses them without an agreement (HTTP 403), so items from them are
    # left out of the search results.
    excluded_collections: tuple[str, ...] = ()


SERVICES = {
    # `orto-dsm-cog` is the paid surface model from aerial images (DSM), listed among the
    # orthophotos.
    "ortofoto": Service(
        "ortofoto", "Ortofoto", "/stac-bild/v1", True, excluded_collections=("orto-dsm-cog",)
    ),
    # Only the free ground model: the surface model (dsm-cog) is a paid product that
    # the API lists for everyone but the download server refuses (HTTP 403).
    "hojd": Service("hojd", "Höjddata (markhöjdmodell)", "/stac-hojd/v1", False, collection="dtm-cog"),
    "laser": Service(
        "laser",
        "Laserdata (punktmoln)",
        "/stac-hojd/v1",
        False,
        collection="dsm-skoglig-copc",
        point_cloud=True,
    ),
}
DEFAULT_SERVICE = "ortofoto"


def search_base_url(service_key: str) -> str:
    return API_URL + SERVICES[service_key].path
