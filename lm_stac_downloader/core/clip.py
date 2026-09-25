"""Partial downloads: clip a remote COG to an area with GDAL.

The rasters served by Lantmäteriet are Cloud Optimized GeoTIFFs (512 x 512
tiles with overviews), so GDAL can read just the tiles that cover an area over
HTTP range requests instead of fetching the whole file. GDAL does not know
about QGIS' authentication, so the `Authorization` header is taken from the QGIS
authentication manager and handed over as a thread-local GDAL option.
"""

from __future__ import annotations

import os
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


def clip_path(output_dir: Path, item: StacItem, bounds: Bounds) -> Path:
    stem = Path(item.filename).stem
    name = f"{stem}_utsnitt_{round(bounds[0])}_{round(bounds[1])}_{round(bounds[2])}_{round(bounds[3])}.tif"
    return output_dir / item.collection / name


class ClipTask(QgsTask):
    # Emitted in the main thread via QgsTask.finished → safe for UI work.
    completed = pyqtSignal(list, list, bool)  # paths, failure messages, cancelled
    # file index (1-based), file count, file name, percent of the current file
    progress_info = pyqtSignal(int, int, str, int)

    def __init__(self, jobs: list[tuple[StacItem, Bounds]], authcfg: str, output_dir: Path):
        super().__init__(f"LM-STAC: hämtar {len(jobs)} utsnitt", QgsTask.Flag.CanCancel)
        self.jobs = jobs
        self.authcfg = authcfg
        self.output_dir = output_dir
        self.paths: list[str] = []
        self.failures: list[str] = []

    def run(self) -> bool:
        for index, (item, bounds) in enumerate(self.jobs, start=1):
            if self.isCanceled():
                return False
            try:
                self._clip(index, item, bounds)
            except Exception as e:  # noqa: BLE001 — report any failure per file
                self.failures.append(f"{item.filename}: {e}")
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

    def _clip(self, index: int, item: StacItem, bounds: Bounds) -> None:
        final = clip_path(self.output_dir, item, bounds)
        if final.exists():
            self.paths.append(str(final))
            return
        final.parent.mkdir(parents=True, exist_ok=True)
        part = final.with_name(final.name + ".part")

        options = {
            "GDAL_HTTP_HEADERS": f"Authorization: {self._authorization(item.href)}",
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
            "GDAL_HTTP_TIMEOUT": "60",
            "GDAL_HTTP_MAX_RETRY": "3",
        }
        # Thread-local, so nothing leaks into QGIS or other plugins.
        for key, value in options.items():
            gdal.SetThreadLocalConfigOption(key, value)
        try:
            source = gdal.Open("/vsicurl/" + item.href)
            if source is None:
                raise RuntimeError(gdal.GetLastErrorMsg() or "kunde inte öppna filen")
            band = source.GetRasterBand(1)
            predictor = 3 if gdal.GetDataTypeName(band.DataType).startswith("Float") else 2

            def progress(fraction, _message, _data) -> int:
                self.progress_info.emit(index, len(self.jobs), item.filename, int(fraction * 100))
                return 0 if self.isCanceled() else 1

            minx, miny, maxx, maxy = bounds
            translate = gdal.TranslateOptions(
                format="GTiff",
                projWin=[minx, maxy, maxx, miny],
                creationOptions=["COMPRESS=DEFLATE", f"PREDICTOR={predictor}", "TILED=YES", "BIGTIFF=IF_SAFER"],
                callback=progress,
            )
            result = gdal.Translate(str(part), source, options=translate)
            if result is None:
                if self.isCanceled():
                    part.unlink(missing_ok=True)
                    return
                raise RuntimeError(gdal.GetLastErrorMsg() or "klippningen misslyckades")
            result = None  # flush to disk before renaming
            source = None
            os.replace(part, final)
            self.paths.append(str(final))
        finally:
            part.unlink(missing_ok=True)
            for key in options:
                gdal.SetThreadLocalConfigOption(key, None)

    def finished(self, result: bool) -> None:
        cancelled = self.isCanceled()
        for failure in self.failures:
            QgsMessageLog.logMessage(failure, PLUGIN_NAME, Qgis.MessageLevel.Warning)
        self.completed.emit(self.paths, self.failures, cancelled)
