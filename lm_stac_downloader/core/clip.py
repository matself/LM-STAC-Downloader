"""Partial downloads: clip a remote COG to an area with GDAL.

The rasters served by Lantmäteriet are Cloud Optimized GeoTIFFs (512 x 512
tiles with overviews), so GDAL can read just the tiles that cover an area over
HTTP range requests instead of fetching the whole file. GDAL does not know
about QGIS' authentication, so the `Authorization` header is taken from the QGIS
authentication manager and handed over as a thread-local GDAL option.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from osgeo import gdal
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMessageLog,
    QgsProject,
    QgsRectangle,
    QgsTask,
)
from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest

from ..config import PLUGIN_NAME, SEARCH_CRS
from .items import StacItem

# Renew the access token this often during a long clip (tokens last about an hour).
TOKEN_REFRESH_SECONDS = 600

Bounds = tuple[float, float, float, float]  # minx, miny, maxx, maxy in the item's CRS


def clip_bounds(item: StacItem, area: QgsRectangle) -> Bounds | None:
    """The part of `item` that `area` (WGS 84) covers, in the item's own CRS.

    Must run on the main thread (it uses the project's transform context).
    Returns None when the area misses the tile or its CRS/extent is unknown.
    """
    if not item.crs or len(item.proj_bbox) != 4:
        return None
    transform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem(SEARCH_CRS),
        QgsCoordinateReferenceSystem(item.crs),
        QgsProject.instance(),
    )
    rect = transform.transformBoundingBox(area)
    tile = item.proj_bbox
    minx, miny = max(rect.xMinimum(), tile[0]), max(rect.yMinimum(), tile[1])
    maxx, maxy = min(rect.xMaximum(), tile[2]), min(rect.yMaximum(), tile[3])
    if minx >= maxx or miny >= maxy:
        return None
    return minx, miny, maxx, maxy


def covered_fraction(item: StacItem, bounds: Bounds) -> float:
    """Share of the tile's area that `bounds` covers (0-1)."""
    tile = item.proj_bbox
    tile_area = (tile[2] - tile[0]) * (tile[3] - tile[1])
    if tile_area <= 0:
        return 1.0
    return (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) / tile_area


def mosaic_path(output_dir: Path, collection: str, bounds: Bounds) -> Path:
    name = f"{collection}_utsnitt_{round(bounds[0])}_{round(bounds[1])}_{round(bounds[2])}_{round(bounds[3])}.tif"
    return output_dir / collection / name


def union_bounds(all_bounds: list[Bounds]) -> Bounds:
    return (
        min(b[0] for b in all_bounds),
        min(b[1] for b in all_bounds),
        max(b[2] for b in all_bounds),
        max(b[3] for b in all_bounds),
    )


class ClipTask(QgsTask):
    # Emitted in the main thread via QgsTask.finished → safe for UI work.
    completed = pyqtSignal(list, list, bool)  # paths, failure messages, cancelled
    # file index (1-based), file count, file name, percent of the current file
    progress_info = pyqtSignal(int, int, str, int)

    def __init__(self, jobs: list[tuple[StacItem, Bounds]], authcfg: str, output_dir: Path):
        super().__init__(f"Geodata: hämtar {len(jobs)} utsnitt", QgsTask.Flag.CanCancel)
        self.jobs = jobs
        self.authcfg = authcfg
        self.output_dir = output_dir
        self.paths: list[str] = []
        self.failures: list[str] = []

    def run(self) -> bool:
        # One output per collection (and CRS): the tiles the area touches are
        # mosaicked into a single file, which is what a user drawing an area expects.
        groups: dict[tuple, list[tuple[StacItem, Bounds]]] = {}
        for item, bounds in self.jobs:
            groups.setdefault((item.collection, item.crs), []).append((item, bounds))
        for index, ((collection, _crs), members) in enumerate(groups.items(), start=1):
            if self.isCanceled():
                return False
            try:
                self._clip_group(index, len(groups), collection, members)
            except Exception as e:  # noqa: BLE001 — report any failure per group
                self.failures.append(f"{collection}: {e}")
        return True

    def _authorization(self, href: str) -> str:
        """A fresh Authorization header value from the QGIS auth manager."""
        request = QNetworkRequest(QUrl(href))
        result = QgsApplication.authManager().updateNetworkRequest(request, self.authcfg)
        ok, request = result if isinstance(result, tuple) else (result, request)
        header = bytes(request.rawHeader(b"Authorization")).decode()
        if not ok or not header:
            raise RuntimeError("kunde inte hämta inloggning från QGIS autentiseringshanterare")
        return header

    def _clip_group(self, index: int, count: int, collection: str, members: list) -> None:
        bounds = union_bounds([b for _item, b in members])
        final = mosaic_path(self.output_dir, collection, bounds)
        if final.exists():
            self.paths.append(str(final))
            return
        final.parent.mkdir(parents=True, exist_ok=True)
        part = final.with_name(final.name + ".part")
        vrt_path = f"/vsimem/lm_stac_{id(self)}_{index}.vrt"
        label = f"{collection} ({len(members)} {'ruta' if len(members) == 1 else 'rutor'})"
        first_href = members[0][0].href

        options = {
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
            "GDAL_HTTP_TIMEOUT": "60",
            "GDAL_HTTP_MAX_RETRY": "3",
        }
        # Thread-local, so nothing leaks into QGIS or other plugins.
        for key, value in options.items():
            gdal.SetThreadLocalConfigOption(key, value)
        gdal.SetThreadLocalConfigOption("GDAL_HTTP_HEADERS", f"Authorization: {self._authorization(first_href)}")
        last_refresh = time.monotonic()
        vrt = source = result = None
        try:
            vrt = gdal.BuildVRT(vrt_path, ["/vsicurl/" + item.href for item, _b in members])
            if vrt is None:
                raise RuntimeError(gdal.GetLastErrorMsg() or "kunde inte öppna filerna")
            predictor = 3 if gdal.GetDataTypeName(vrt.GetRasterBand(1).DataType).startswith("Float") else 2

            def progress(fraction, _message, _data) -> int:
                nonlocal last_refresh
                self.progress_info.emit(index, count, label, int(fraction * 100))
                # GDAL reads the header option on every request, so a long clip can
                # outlive the access token by renewing it here.
                if time.monotonic() - last_refresh > TOKEN_REFRESH_SECONDS:
                    gdal.SetThreadLocalConfigOption(
                        "GDAL_HTTP_HEADERS", f"Authorization: {self._authorization(first_href)}"
                    )
                    last_refresh = time.monotonic()
                return 0 if self.isCanceled() else 1

            minx, miny, maxx, maxy = bounds
            translate = gdal.TranslateOptions(
                format="GTiff",
                projWin=[minx, maxy, maxx, miny],
                creationOptions=["COMPRESS=DEFLATE", f"PREDICTOR={predictor}", "TILED=YES", "BIGTIFF=IF_SAFER"],
                callback=progress,
            )
            result = gdal.Translate(str(part), vrt, options=translate)
            if result is None:
                if self.isCanceled():
                    return
                raise RuntimeError(gdal.GetLastErrorMsg() or "klippningen misslyckades")
            result = None  # flush to disk before renaming
            vrt = None
            os.replace(part, final)
            self.paths.append(str(final))
        finally:
            result = vrt = source = None
            gdal.Unlink(vrt_path)
            part.unlink(missing_ok=True)
            for key in (*options, "GDAL_HTTP_HEADERS"):
                gdal.SetThreadLocalConfigOption(key, None)

    def finished(self, result: bool) -> None:
        cancelled = self.isCanceled()
        for failure in self.failures:
            QgsMessageLog.logMessage(failure, PLUGIN_NAME, Qgis.MessageLevel.Warning)
        self.completed.emit(self.paths, self.failures, cancelled)
