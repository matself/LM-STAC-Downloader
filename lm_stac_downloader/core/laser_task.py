"""Background task: clip remote COPC point clouds to an area with `pdal`."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - runs QGIS' own pdal with a fixed argument list, no shell
import sys
import tempfile
from pathlib import Path

from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsTask
from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest

from ..config import PLUGIN_NAME
from .items import StacItem
from .laser import Bounds, clip_path, clip_pipeline, merge_command, pipeline_json, union_bounds

# Give up on one pdal run after this long.
PDAL_TIMEOUT_SECONDS = 1800


def qgis_pdal_dirs() -> list[Path]:
    """Directories where the QGIS installation keeps `pdal`."""
    prefix = Path(QgsApplication.prefixPath())
    # Windows: <root>/apps/qgis[-ltr] with <root>/bin; Linux/macOS: <prefix>/bin.
    return [prefix.parent.parent / "bin", prefix / "bin", Path(sys.executable).parent]


class LaserClipTask(QgsTask):
    # Emitted in the main thread via QgsTask.finished → safe for UI work.
    completed = pyqtSignal(list, list, bool)  # paths, failure messages, cancelled
    # tile index (1-based), tile count, tile name
    progress_info = pyqtSignal(int, int, str)

    def __init__(self, jobs: list[tuple[StacItem, Bounds]], authcfg: str, output_dir: Path, pdal: str):
        super().__init__(f"Geodata: hämtar {len(jobs)} laserutsnitt", QgsTask.Flag.CanCancel)
        self.jobs = jobs
        self.authcfg = authcfg
        self.output_dir = output_dir
        self.pdal = pdal
        self.paths: list[str] = []
        self.failures: list[str] = []
        self._process: subprocess.Popen | None = None

    def cancel(self) -> None:
        process = self._process
        if process and process.poll() is None:
            process.kill()
        super().cancel()

    def run(self) -> bool:
        collection = self.jobs[0][0].collection
        final = clip_path(self.output_dir, collection, union_bounds([b for _i, b in self.jobs]))
        if final.exists():
            self.paths.append(str(final))
            return True
        final.parent.mkdir(parents=True, exist_ok=True)
        # Private working folder: the pipeline files hold a bearer token.
        work = Path(tempfile.mkdtemp(prefix="lm_stac_laser_"))
        try:
            pieces: list[Path] = []
            for index, (item, bounds) in enumerate(self.jobs, start=1):
                if self.isCanceled():
                    return False
                self.progress_info.emit(index, len(self.jobs), item.id)
                self.setProgress(100 * (index - 1) / len(self.jobs))
                piece = work / f"piece_{index}.laz"
                try:
                    self._clip_tile(item, bounds, work, piece)
                    pieces.append(piece)
                except Exception as e:  # noqa: BLE001 — report any failure per tile
                    if self.isCanceled():
                        return False
                    self.failures.append(f"{item.id}: {e}")
            if not pieces:
                return True
            part = final.with_name(final.stem + ".part.laz")
            if len(pieces) == 1:
                shutil.move(str(pieces[0]), part)
            else:
                self._run(merge_command(self.pdal, pieces, part))
            os.replace(part, final)
            self.paths.append(str(final))
            return True
        except Exception as e:  # noqa: BLE001
            if not self.isCanceled():
                self.failures.append(str(e))
            return True
        finally:
            shutil.rmtree(work, ignore_errors=True)
            final.with_name(final.stem + ".part.laz").unlink(missing_ok=True)

    def _authorization(self, href: str) -> str:
        """A fresh Authorization header value from the QGIS auth manager."""
        request = QNetworkRequest(QUrl(href))
        result = QgsApplication.authManager().updateNetworkRequest(request, self.authcfg)
        ok, request = result if isinstance(result, tuple) else (result, request)
        header = bytes(request.rawHeader(b"Authorization")).decode()
        if not ok or not header:
            raise RuntimeError("kunde inte hämta inloggning från QGIS autentiseringshanterare")
        return header

    def _clip_tile(self, item: StacItem, bounds: Bounds, work: Path, output: Path) -> None:
        pipeline = clip_pipeline(item.href, self._authorization(item.href), bounds, output)
        spec = work / f"{output.stem}.json"
        # Create with owner-only permissions before the token goes in.
        fd = os.open(spec, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(pipeline_json(pipeline))
            self._run([self.pdal, "pipeline", str(spec)])
        finally:
            spec.unlink(missing_ok=True)
        if not output.exists():
            raise RuntimeError("pdal gav ingen utfil")

    def _run(self, command: list[str]) -> None:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._process = subprocess.Popen(  # nosec B603 - fixed argument list, no shell
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        )
        try:
            _out, err = self._process.communicate(timeout=PDAL_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.communicate()
            raise RuntimeError("pdal tog för lång tid") from None
        if self._process.returncode != 0 and not self.isCanceled():
            # pdal does not echo the pipeline, so no token ends up in the message.
            lines = (err or "").strip().splitlines()
            raise RuntimeError(lines[-1][:300] if lines else "pdal misslyckades")

    def finished(self, result: bool) -> None:
        for failure in self.failures:
            QgsMessageLog.logMessage(failure, PLUGIN_NAME, Qgis.MessageLevel.Warning)
        self.completed.emit(self.paths, self.failures, self.isCanceled())
