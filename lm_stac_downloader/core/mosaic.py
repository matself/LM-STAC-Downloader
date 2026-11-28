"""Which tiles go into the same clip file, and what that file is called.

The tiles an area touches are mosaicked into one file per collection, CRS and
spectral type. Where tiles from different flight years cover the same ground,
only one of them would be visible in a mosaic, so such a set is split into one
file per year. Years that only lie next to each other stay in one file.

This module has no QGIS imports, so it can be tested on its own.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .items import StacItem

Bounds = tuple[float, float, float, float]  # minx, miny, maxx, maxy in the item's CRS
Job = tuple[StacItem, Bounds]

# Neighbouring tiles share an edge; only a wider overlap than this (in CRS units) hides data.
_EDGE_TOLERANCE = 0.01


@dataclass(frozen=True)
class Group:
    """The tiles of one output file."""

    collection: str
    spectral: str | None
    members: tuple[Job, ...]

    @property
    def bounds(self) -> Bounds:
        return union_bounds([bounds for _item, bounds in self.members])

    @property
    def years(self) -> str:
        """The flight year, or the first and last one ("1957-1959"). Empty if unknown."""
        found = sorted({item.year for item, _bounds in self.members if item.year})
        if not found:
            return ""
        return str(found[0]) if len(found) == 1 else f"{found[0]}-{found[-1]}"

    @property
    def label(self) -> str:
        # Only imagery has a spectral type; the date of an elevation tile is not a flight year.
        parts = [self.collection, self.spectral, self.years if self.spectral else ""]
        return " ".join(part for part in parts if part)


def union_bounds(all_bounds: list[Bounds]) -> Bounds:
    return (
        min(b[0] for b in all_bounds),
        min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds),
        max(b[3] for b in all_bounds),
    )


def _overlap(a: Bounds, b: Bounds) -> bool:
    width = min(a[2], b[2]) - max(a[0], b[0])
    height = min(a[3], b[3]) - max(a[1], b[1])
    return width > _EDGE_TOLERANCE and height > _EDGE_TOLERANCE


def _years_hide_each_other(members: list[Job]) -> bool:
    return any(
        item.year != other.year and _overlap(bounds, other_bounds)
        for index, (item, bounds) in enumerate(members)
        for other, other_bounds in members[index + 1 :]
    )


def group_jobs(jobs: list[Job]) -> list[Group]:
    """Split (item, clip bounds) pairs into the output files to write."""
    # Colour (rgb) and infrared (cir) images of the same tile must stay apart.
    by_kind: dict[tuple, list[Job]] = {}
    for item, bounds in jobs:
        by_kind.setdefault((item.collection, item.crs, item.spectral), []).append((item, bounds))

    groups = []
    for (collection, _crs, spectral), members in by_kind.items():
        parts = [members]
        if _years_hide_each_other(members):
            by_year: dict[int | None, list[Job]] = {}
            for job in members:
                by_year.setdefault(job[0].year, []).append(job)
            parts = [by_year[year] for year in sorted(by_year, key=lambda y: y or 0)]
        groups.extend(Group(collection, spectral, tuple(part)) for part in parts)
    return groups


def mosaic_path(output_dir: Path, group: Group) -> Path:
    """`<collection>[_<type>_<years>]_utsnitt_<minx>_<miny>_<maxx>_<maxy>_<checksum>.tif`

    The checksum covers the ids of the tiles, so that a file made from other tiles
    for the same area is never taken to be this one.
    """
    ids = "\n".join(sorted(item.id for item, _bounds in group.members))
    checksum = hashlib.sha256(ids.encode()).hexdigest()[:8]
    kind = f"_{group.spectral}" if group.spectral else ""
    if group.spectral and group.years:
        kind += f"_{group.years}"
    corners = "_".join(str(round(value)) for value in group.bounds)
    name = f"{group.collection}{kind}_utsnitt_{corners}_{checksum}.tif"
    return output_dir / group.collection / name
