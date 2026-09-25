"""Light-weight view of a STAC item with a downloadable raster asset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

    @property
    def filename(self) -> str:
        return self.href.rstrip("/").rsplit("/", 1)[-1]

    @property
    def tile_label(self) -> str:
        """Tile size from the extent, e.g. "2,5 km-ruta" or "10 km-blad". Empty if unknown."""
        if len(self.proj_bbox) != 4:
            return ""
        km = (self.proj_bbox[2] - self.proj_bbox[0]) / 1000
        return f"{km:g}".replace(".", ",") + (" km-blad" if km >= 10 else " km-ruta")

    @property
    def kind(self) -> str:
        """What sets this item apart from its siblings: spectral type or tile size."""
        return self.spectral or (self.tile_label if self.model else "")


def parse_item(feature: dict[str, Any]) -> StacItem | None:
    """Return None for items without a downloadable raster `data` asset.

    stac-hojd also serves point clouds (COPC/LAZ), which are not rasters.
    """
    data = (feature.get("assets") or {}).get("data")
    if not data or not data.get("href"):
        return None
    if "tiff" not in (data.get("type") or "").lower():
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
    )


def _year(value: Any) -> int | None:
    try:
        return int(str(value)[:4])
    except (TypeError, ValueError):
        return None
