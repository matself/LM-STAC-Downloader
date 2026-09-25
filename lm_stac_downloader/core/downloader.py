"""Sequential file downloads with QgsFileDownloader.

QgsFileDownloader streams to disk, which matters here: one orthophoto file is
hundreds of MB. It runs on the main thread's event loop, so the UI stays
responsive and progress arrives as signals. Files are written to `<name>.part`
and renamed on success, so a cancelled download never looks complete.
"""

from __future__ import annotations

import os
from pathlib import Path

from qgis.core import QgsFileDownloader
from qgis.PyQt.QtCore import QObject, QUrl, pyqtSignal

from .items import StacItem


def target_path(output_dir: Path, item: StacItem) -> Path:
    return output_dir / item.collection / item.filename


class DownloadQueue(QObject):
    # file index (1-based), file count, current file name, bytes received, bytes total
    progress = pyqtSignal(int, int, str, "qlonglong", "qlonglong")
    # downloaded (or already present) paths, failure messages, cancelled
    finished = pyqtSignal(list, list, bool)

    def __init__(self, items: list[StacItem], authcfg: str, output_dir: Path, parent=None):
        super().__init__(parent)
        self.items = items
        self.authcfg = authcfg
        self.output_dir = output_dir
        self.paths: list[str] = []
        self.failures: list[str] = []
        self._index = -1
        self._downloader: QgsFileDownloader | None = None
        self._cancelled = False

    def start(self) -> None:
        self._next()

    def cancel(self) -> None:
        self._cancelled = True
        if self._downloader:
            self._downloader.cancelDownload()
        else:
            self._done()

    def _next(self) -> None:
        self._downloader = None
        self._index += 1
        if self._cancelled or self._index >= len(self.items):
            self._done()
            return

        item = self.items[self._index]
        final = target_path(self.output_dir, item)
        if final.exists() and (item.size is None or final.stat().st_size == item.size):
            self.paths.append(str(final))
            self.progress.emit(self._index + 1, len(self.items), item.filename, 1, 1)
            self._next()
            return

        final.parent.mkdir(parents=True, exist_ok=True)
        part = final.with_name(final.name + ".part")
        downloader = QgsFileDownloader(QUrl(item.href), str(part), self.authcfg, True)
        self._downloader = downloader
        downloader.downloadProgress.connect(
            lambda received, total, item=item: self.progress.emit(
                self._index + 1, len(self.items), item.filename, received, total
            )
        )
        downloader.downloadCompleted.connect(
            lambda _url, part=part, final=final: self._completed(part, final)
        )
        downloader.downloadError.connect(lambda errors, item=item: self._error(item, errors))
        downloader.downloadCanceled.connect(lambda part=part: self._discard(part))
        downloader.downloadExited.connect(self._exited)
        downloader.startDownload()

    def _completed(self, part: Path, final: Path) -> None:
        os.replace(part, final)
        self.paths.append(str(final))

    def _error(self, item: StacItem, errors: list) -> None:
        self.failures.append(f"{item.filename}: {'; '.join(str(e) for e in errors)}")

    @staticmethod
    def _discard(part: Path) -> None:
        part.unlink(missing_ok=True)

    def _exited(self) -> None:
        # Always emitted last, whatever the outcome; move on to the next file.
        if self._downloader is not None:
            self._downloader.deleteLater()
        self._next()

    def _done(self) -> None:
        self.finished.emit(self.paths, self.failures, self._cancelled)
