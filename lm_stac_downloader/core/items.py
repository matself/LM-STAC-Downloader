"""Light-weight view of a STAC item with a downloadable raster or point cloud asset."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Laser data ids: `25a002-61375_4400_25` is a 2,5 km tile (northing, easting, size code),
# `25a002-613_44` a 10 km tile (northing, easting).
_TILE_25_ID = re.compile(r"^[^-]+-\d+_\d+_25$")
_TILE_10_ID = re.compile(r"^[^-]+-\d+_\d+$")


@dataclass(frozen=True)
class StacItem:
    id: str
    collection: str
    year: int | None
    resolution: float | None
    size: int | None
    href: str
    bbox: tuple[float, ...]
    geometry: dict[str, Any] | None
    crs: str | None
    proj_bbox: tuple[float, ...] = ()
    cog: bool = False
    spectral: str | None = None  # e.g. "rgb" or "cir" for orthophotos
    model: str | None = None  # e.g. "markhöjdmodell" for elevation models
    changed: str | None = None  # date the data was last changed (elevation models)
    point_cloud: bool = False  # COPC/LAZ instead of a raster
    points: int | None = None  # number of points (`pc:count`), point clouds only

    @property
    def filename(self) -> str:
        return self.href.rstrip("/").rsplit("/", 1)[-1]

    @property
    def tile_label(self) -> str:
        """Tile size, e.g. "2,5 km-ruta" or "10 km-ruta". Empty if unknown.

        The extent cannot be trusted for the 10 km tiles (`dtm-cog` and the laser data):
        tiles at the coast and the border are cut to the land that exists, so they can be
        10 x 5, 7,5 x 10 or 2,5 x 5 km. The size follows the collection or the id where it
        is known, and a tile smaller than 10 x 10 km is marked "(beskuren)" (cut).
        """
        if self.collection.startswith("mhm-"):
            return "2,5 km-ruta"
        if self.collection == "dtm-cog" or (self.point_cloud and _TILE_10_ID.match(self.id)):
            return "10 km-ruta" + self._cut_suffix()
        if self.point_cloud and _TILE_25_ID.match(self.id):
            return "2,5 km-ruta"
        if len(self.proj_bbox) != 4:
            return ""
        km = (self.proj_bbox[2] - self.proj_bbox[0]) / 1000
        return f"{km:g}".replace(".", ",") + " km-ruta"

    def _cut_suffix(self) -> str:
        if len(self.proj_bbox) != 4:
            return ""
        width = self.proj_bbox[2] - self.proj_bbox[0]
        height = self.proj_bbox[3] - self.proj_bbox[1]
        return " (beskuren)" if width < 10000 or height < 10000 else ""

    @property
    def kind(self) -> str:
        """What sets this item apart from its siblings: spectral type or tile size."""
        return self.spectral or (self.tile_label if self.model or self.point_cloud else "")


def is_point_cloud_type(media_type: str | None) -> bool:
    """True for COPC/LAZ media types such as `application/vnd.laszip+copc`."""
    media_type = (media_type or "").lower()
    return "copc" in media_type or "laszip" in media_type


def parse_item(feature: dict[str, Any], point_cloud: bool = False) -> StacItem | None:
    """Return None for items without a downloadable `data` asset of the wanted kind.

    stac-hojd serves both elevation rasters and point clouds (COPC/LAZ). With
    `point_cloud` False only rasters pass, with True only point clouds.
    """
    data = (feature.get("assets") or {}).get("data")
    if not data or not data.get("href"):
        return None
    media_type = (data.get("type") or "").lower()
    if point_cloud:
        if not is_point_cloud_type(media_type):
            return None
    elif "tiff" not in media_type:
        return None
    props = feature.get("properties") or {}
    year = props.get("flygar")
    if year is None:
        year = _year(props.get("datetime") or props.get("start_datetime"))
    return StacItem(
        id=feature["id"],
        collection=feature.get("collection", ""),
        year=year,
        resolution=props.get("upplosning"),
        size=data.get("file:size"),
        href=data["href"],
        bbox=tuple(feature.get("bbox") or ()),
        geometry=feature.get("geometry"),
        crs=data.get("proj:code") or props.get("proj:code"),
        proj_bbox=tuple(data.get("proj:bbox") or props.get("proj:bbox") or ()),
        cog="cloud-optimized" in (data.get("type") or "").lower(),
        spectral=props.get("spektraltyp"),
        model=props.get("hojdmodelltyp"),
        changed=props.get("andringsdatum"),
        point_cloud=point_cloud,
        points=_int(props.get("pc:count", data.get("pc:count"))) if point_cloud else None,
    )


def _year(value: Any) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
