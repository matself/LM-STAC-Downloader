"""Client-side filtering of orthophoto search hits.

A selection maps a dimension to the set of values the user has ticked. Within a
dimension the values add up (0.16 m or 0.25 m); the dimensions narrow each other
(0.25 m and infrared). A dimension with nothing ticked lets everything through.

This module has no QGIS imports, so it can be tested on its own.
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlparse

from .items import StacItem

RESOLUTION = "resolution"
IMAGE_TYPE = "image_type"
SERIES = "series"

COLOUR, INFRARED, PANCHROMATIC = "colour", "infrared", "panchromatic"
AREA, TOWN, HISTORICAL = "area", "town", "historical"

# A four-band `rgbi` image can be shown both as colour and as colour infrared.
_IMAGE_TYPES = {
    "rgb": {COLOUR},
    "cir": {INFRARED},
    "rgbi": {COLOUR, INFRARED},
    "pan": {PANCHROMATIC},
}


def image_types(item: StacItem) -> set[str]:
    return _IMAGE_TYPES.get((item.spectral or "").lower(), set())


def series(item: StacItem) -> str:
    """Which orthophoto series a tile belongs to.

    Town (urban area) orthophotos are recognised by the folder of the file
    (`tatort`, `tatort_i`, `tatort_m`), so no place names are hard-coded.
    """
    if item.collection.startswith("orto-historiska"):
        return HISTORICAL
    folders = urlparse(item.href).path.lower().split("/")[:-1]
    if any(folder.startswith("tatort") for folder in folders):
        return TOWN
    return AREA


def values(item: StacItem, dimension: str) -> set:
    if dimension == RESOLUTION:
        return set() if item.resolution is None else {item.resolution}
    if dimension == IMAGE_TYPE:
        return image_types(item)
    if dimension == SERIES:
        return {series(item)}
    raise ValueError(f"unknown filter dimension: {dimension}")


def available(items: Iterable[StacItem], dimension: str) -> set:
    """The values present among `items`, i.e. the options worth offering."""
    found: set = set()
    for item in items:
        found |= values(item, dimension)
    return found


def matches(item: StacItem, selection: dict[str, set]) -> bool:
    return all(not chosen or values(item, dimension) & chosen for dimension, chosen in selection.items())


def select(items: Iterable[StacItem], selection: dict[str, set], limit: int) -> tuple[list[StacItem], int]:
    """The hits to show, and how many match the selection.

    Nothing is shown when more than `limit` match: a cut-off list would not tell
    what is missing.
    """
    matching = [item for item in items if matches(item, selection)]
    return (matching if len(matching) <= limit else []), len(matching)
