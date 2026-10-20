"""Point cloud clipping with PDAL: the parts that need neither QGIS nor a network.

The point clouds are COPC (cloud optimized point cloud) files, an octree that a
reader can fetch with HTTP range requests. `pdal pipeline` with `readers.copc`
and a `bounds` option therefore reads only the part of a 157 MB tile that an area
covers. The download host requires a bearer token, which `readers.copc` takes as
a file specification with `headers`.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable, Iterable
from pathlib import Path

from .items import StacItem

Bounds = tuple[float, float, float, float]  # minx, miny, maxx, maxy in SWEREF 99 TM

# The COPC items say EPSG:5845 (SWEREF 99 TM + RH2000 height). PDAL's `bounds`
# are in the horizontal CRS, which is the same as EPSG:3006.
HORIZONTAL_CRS = "EPSG:3006"


def pdal_executable_names() -> tuple[str, ...]:
    return ("pdal.exe", "pdal") if os.name == "nt" else ("pdal",)


def find_pdal(
    search_dirs: Iterable[str | Path],
    which: Callable[[str], str | None] = shutil.which,
) -> str | None:
    """Path to `pdal`: first in the given directories (QGIS' own `bin`), then on PATH."""
    for directory in search_dirs:
        for name in pdal_executable_names():
            candidate = Path(directory) / name
            if candidate.is_file():
                return str(candidate)
    return which("pdal")


def bounds_string(bounds: Bounds) -> str:
    """PDAL's `bounds` syntax, e.g. `([453000,453100],[6395800,6395900])`."""
    minx, miny, maxx, maxy = bounds
    return f"([{minx:.3f},{maxx:.3f}],[{miny:.3f},{maxy:.3f}])"


def clip_pipeline(href: str, authorization: str, bounds: Bounds, output: str | Path) -> dict:
    """The PDAL pipeline that reads `bounds` of the remote COPC at `href` into a LAZ file.

    Contains the authorization header: write it to a private file and delete it
    straight after use.
    """
    return {
        "pipeline": [
            {
                "type": "readers.copc",
                "filename": {"path": href, "headers": {"Authorization": authorization}},
                "bounds": bounds_string(bounds),
            },
            {"type": "writers.las", "filename": str(output), "compression": "laszip"},
        ]
    }


def pipeline_json(pipeline: dict) -> str:
    return json.dumps(pipeline)


def merge_command(pdal: str, inputs: list[str | Path], output: str | Path) -> list[str]:
    """`pdal merge in1 in2 … out` (the last argument is the output)."""
    return [pdal, "merge", *map(str, inputs), str(output)]


def tile_bounds(item: StacItem, area: Bounds) -> Bounds | None:
    """The part of `item` that `area` (SWEREF 99 TM) covers.

    None when they do not overlap, or when the tile's extent is unknown.
    """
    if len(item.proj_bbox) != 4:
        return None
    tile = item.proj_bbox
    minx, miny = max(area[0], tile[0]), max(area[1], tile[1])
    maxx, maxy = min(area[2], tile[2]), min(area[3], tile[3])
    if minx >= maxx or miny >= maxy:
        return None
    return minx, miny, maxx, maxy


def union_bounds(all_bounds: list[Bounds]) -> Bounds:
    return (
        min(b[0] for b in all_bounds),
        min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds),
        max(b[3] for b in all_bounds),
    )


def clip_path(output_dir: Path, collection: str, bounds: Bounds) -> Path:
    name = f"{collection}_utsnitt_{round(bounds[0])}_{round(bounds[1])}_{round(bounds[2])}_{round(bounds[3])}.laz"
    return output_dir / collection / name

