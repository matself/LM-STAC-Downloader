"""Background task: save the metadata files (seamlines) of orthophoto tiles.

The `metadata` asset of an orthophoto is a small GeoJSON file (tens of kB) with one
polygon per aerial photo in the mosaic, with the photo id and the exact time. It is
served from a public path, so no credentials are needed.
"""

from __future__ import annotations

from pathlib import Path

from qgis.core import Qgis, QgsBlockingNetworkRequest, QgsFeedback, QgsMessageLog, QgsTask
from qgis.PyQt.QtCore import QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest

from ..config import PLUGIN_NAME
from .items import StacItem


def metadata_path(output_dir: Path, item: StacItem) -> Path:
    """Next to the image: `<output>/<collection>/<tile>_flygbild.json`."""
    return output_dir / item.collection / item.metadata_filename


class MetadataTask(QgsTask):
    completed = pyqtSignal(list, list)  # saved paths, failure messages

    def __init__(self, items: list[StacItem], output_dir: Path):
        super().__init__("Geodata: hämtar metadata", QgsTask.Flag.CanCancel)
        self.items = [item for item in items if item.metadata_href]
        self.output_dir = output_dir
        self.paths: list[str] = []
        self.failures: list[str] = []
        self._feedback = QgsFeedback()

    def cancel(self) -> None:
        self._feedback.cancel()
        super().cancel()

    def run(self) -> bool:
        for number, item in enumerate(self.items, start=1):
            if self.isCanceled():
                return False
            target = metadata_path(self.output_dir, item)
            if target.exists():
                self.paths.append(str(target))
            else:
                self._fetch(item, target)
            self.setProgress(100 * number / len(self.items))
        return True

    def _fetch(self, item: StacItem, target: Path) -> None:
        blocking = QgsBlockingNetworkRequest()
        error = blocking.get(QNetworkRequest(QUrl(item.metadata_href)), True, self._feedback)
        reply = blocking.reply()
        if error != QgsBlockingNetworkRequest.ErrorCode.NoError:
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            message = f"{item.metadata_filename}: HTTP {status or '?'} {blocking.errorMessage()}".strip()
            self.failures.append(message)
            QgsMessageLog.logMessage(message, PLUGIN_NAME, Qgis.MessageLevel.Warning)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + ".part")
        part.write_bytes(bytes(reply.content()))
        part.replace(target)
        self.paths.append(str(target))

    def finished(self, result: bool) -> None:
        if result or not self.isCanceled():
            self.completed.emit(self.paths, self.failures)
