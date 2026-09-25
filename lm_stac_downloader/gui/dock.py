"""Main dock widget: pick auth, service and area, search, select and download."""

from __future__ import annotations

from pathlib import Path

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.gui import QgsAuthConfigSelect, QgsFileWidget, QgsMapToolExtent, QgsRubberBand
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import (
    DEFAULT_SERVICE,
    MAX_RESULTS,
    PLUGIN_NAME,
    SEARCH_CRS,
    SERVICES,
    SETTINGS_PREFIX,
    WARN_BYTES,
    search_base_url,
)
from ..core.auth import authcfg_exists
from ..core.downloader import DownloadQueue
from ..core.items import StacItem
from ..core.task import SearchTask
from .auth_dialog import CreateAuthDialog

try:  # QGIS >= 3.30
    from qgis.PyQt.QtCore import QMetaType

    _STRING, _INT, _DOUBLE = QMetaType.Type.QString, QMetaType.Type.Int, QMetaType.Type.Double
except (ImportError, AttributeError):  # older QGIS 3 uses QVariant types
    from qgis.PyQt.QtCore import QVariant

    _STRING, _INT, _DOUBLE = QVariant.String, QVariant.Int, QVariant.Double

COL_NAME, COL_COLLECTION, COL_YEAR, COL_RES, COL_SIZE = range(5)
FOOTPRINT_LAYER = "LM-STAC träffar"


def _format_bytes(size: int | None) -> str:
    if size is None:
        return "?"
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


class _SortableItem(QTreeWidgetItem):
    """Tree item that sorts numeric columns by their value, not their text."""

    def __lt__(self, other) -> bool:
        column = self.treeWidget().sortColumn()
        a, b = self.data(column, Qt.ItemDataRole.UserRole), other.data(column, Qt.ItemDataRole.UserRole)
        if a is not None and b is not None:
            return a < b
        return super().__lt__(other)


class StacDock(QDockWidget):
    def __init__(self, iface, parent=None):
        super().__init__(PLUGIN_NAME, parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.settings = QgsSettings()
        self.items: list[StacItem] = []
        self.area: QgsRectangle | None = None  # WGS 84
        self._search_task: SearchTask | None = None
        self._queue: DownloadQueue | None = None
        self._footprints: QgsVectorLayer | None = None
        self._previous_tool = None

        self._tool = QgsMapToolExtent(self.canvas)
        self._tool.extentChanged.connect(self._on_extent_drawn)
        self._tool.deactivated.connect(self._on_tool_deactivated)
        self._band = QgsRubberBand(self.canvas, _polygon_type())
        self._band.setColor(QColor(200, 40, 40, 200))
        self._band.setFillColor(QColor(200, 40, 40, 40))
        self._band.setWidth(2)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.addWidget(self._build_connection_group())
        layout.addWidget(self._build_search_group())
        layout.addWidget(self._build_results_group())
        layout.addWidget(self._build_output_group())
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        self.setWidget(scroll)

        self._restore_settings()
        self._on_service_changed()

    def cleanup(self) -> None:
        if self._queue:
            self._queue.cancel()
        if self._search_task:
            self._search_task.cancel()
        self._band.reset(_polygon_type())
        if self.canvas.mapTool() is self._tool:
            self.canvas.unsetMapTool(self._tool)
        self._save_settings()

    # --- UI construction -------------------------------------------------

    def _build_connection_group(self) -> QGroupBox:
        group = QGroupBox("Anslutning")
        form = QFormLayout(group)
        # QGIS' own auth config picker: users can also create/edit configs here.
        self.auth_select = QgsAuthConfigSelect(self)
        form.addRow("Autentisering", self.auth_select)
        new_auth_btn = QPushButton("Ny Lantmäteriet-inloggning…")
        new_auth_btn.clicked.connect(self._create_auth)
        form.addRow("", new_auth_btn)
        return group

    def _build_search_group(self) -> QGroupBox:
        group = QGroupBox("Sökning")
        layout = QVBoxLayout(group)

        form = QFormLayout()
        self.service_combo = QComboBox()
        for service in SERVICES.values():
            self.service_combo.addItem(service.label, service.key)
        self.service_combo.currentIndexChanged.connect(self._on_service_changed)
        form.addRow("Tjänst", self.service_combo)

        self.year_from = QSpinBox()
        self.year_from.setRange(1950, 2100)
        self.year_to = QSpinBox()
        self.year_to.setRange(1950, 2100)
        year_row = QHBoxLayout()
        year_row.addWidget(self.year_from)
        year_row.addWidget(QLabel("–"))
        year_row.addWidget(self.year_to)
        self.year_widget = QWidget()
        self.year_widget.setLayout(year_row)
        year_row.setContentsMargins(0, 0, 0, 0)
        self.year_label = QLabel("Flygår")
        form.addRow(self.year_label, self.year_widget)
        layout.addLayout(form)

        row = QHBoxLayout()
        view_btn = QPushButton("Använd kartvyn")
        view_btn.clicked.connect(self._use_canvas_extent)
        draw_btn = QPushButton("Rita ruta")
        draw_btn.clicked.connect(self._draw_area)
        row.addWidget(view_btn)
        row.addWidget(draw_btn)
        layout.addLayout(row)

        self.area_label = QLabel("Inget område valt")
        layout.addWidget(self.area_label)

        self.search_btn = QPushButton("Sök")
        self.search_btn.clicked.connect(self._start_search)
        layout.addWidget(self.search_btn)
        self.search_status = QLabel("")
        self.search_status.setWordWrap(True)
        layout.addWidget(self.search_status)
        return group

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("Träffar")
        layout = QVBoxLayout(group)

        self.tree = QTreeWidget()
        self.tree.setRootIsDecorated(False)
        self.tree.setSortingEnabled(True)
        self.tree.setMinimumHeight(200)
        self.tree.setHeaderLabels(["Ruta", "Kollektion", "År", "Upplösning", "Storlek"])
        self.tree.itemChanged.connect(self._update_summary)
        layout.addWidget(self.tree)

        row = QHBoxLayout()
        all_btn = QPushButton("Markera alla")
        all_btn.clicked.connect(lambda: self._set_all_checked(True))
        none_btn = QPushButton("Avmarkera alla")
        none_btn.clicked.connect(lambda: self._set_all_checked(False))
        row.addWidget(all_btn)
        row.addWidget(none_btn)
        layout.addLayout(row)

        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)
        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Hämta")
        layout = QVBoxLayout(group)

        self.output_widget = QgsFileWidget()
        self.output_widget.setStorageMode(QgsFileWidget.StorageMode.GetDirectory)
        layout.addWidget(self.output_widget)

        self.add_to_project = QCheckBox("Lägg till i projektet när klart")
        self.add_to_project.setChecked(True)
        layout.addWidget(self.add_to_project)

        self.download_btn = QPushButton("Hämta valda")
        self.download_btn.clicked.connect(self._start_download)
        layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("Avbryt")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setVisible(False)
        layout.addWidget(self.cancel_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.progress_label = QLabel("")
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)
        return group

    # --- settings --------------------------------------------------------

    def _key(self, name: str) -> str:
        return f"{SETTINGS_PREFIX}/{name}"

    def _restore_settings(self) -> None:
        self.auth_select.setConfigId(self.settings.value(self._key("authcfg"), ""))
        service = self.settings.value(self._key("service"), DEFAULT_SERVICE)
        self.service_combo.setCurrentIndex(max(0, self.service_combo.findData(service)))
        self.year_from.setValue(int(self.settings.value(self._key("year_from"), 2020)))
        self.year_to.setValue(int(self.settings.value(self._key("year_to"), 2026)))
        self.output_widget.setFilePath(self.settings.value(self._key("output"), str(Path.home())))

    def _save_settings(self) -> None:
        self.settings.setValue(self._key("authcfg"), self.auth_select.configId())
        self.settings.setValue(self._key("service"), self.service_combo.currentData())
        self.settings.setValue(self._key("year_from"), self.year_from.value())
        self.settings.setValue(self._key("year_to"), self.year_to.value())
        self.settings.setValue(self._key("output"), self.output_widget.filePath())

    # --- helpers ---------------------------------------------------------

    def _message(self, text: str, level=Qgis.MessageLevel.Info) -> None:
        self.iface.messageBar().pushMessage(PLUGIN_NAME, text, level, 8)

    def _authcfg_or_warn(self) -> str | None:
        authcfg = self.auth_select.configId()
        if not authcfg_exists(authcfg):
            self._message(
                "Välj eller skapa en autentisering först.", Qgis.MessageLevel.Warning
            )
            return None
        return authcfg

    def _create_auth(self) -> None:
        dlg = CreateAuthDialog(self)
        if dlg.exec() and dlg.authcfg:
            self.auth_select.setConfigId(dlg.authcfg)
            self._save_settings()

    def _on_service_changed(self) -> None:
        service = SERVICES[self.service_combo.currentData()]
        self.year_widget.setVisible(service.has_years)
        self.year_label.setVisible(service.has_years)

    # --- area ------------------------------------------------------------

    def _set_area(self, rect: QgsRectangle, crs: QgsCoordinateReferenceSystem) -> None:
        target = QgsCoordinateReferenceSystem(SEARCH_CRS)
        transform = QgsCoordinateTransform(crs, target, QgsProject.instance())
        self.area = transform.transformBoundingBox(rect)
        self._band.reset(_polygon_type())
        self._band.setToGeometry(QgsGeometry.fromRect(rect), crs)
        a = self.area
        self.area_label.setText(
            f"Område: {a.xMinimum():.4f}, {a.yMinimum():.4f} – {a.xMaximum():.4f}, {a.yMaximum():.4f}"
        )

    def _use_canvas_extent(self) -> None:
        self._set_area(self.canvas.extent(), self.canvas.mapSettings().destinationCrs())

    def _draw_area(self) -> None:
        self._previous_tool = self.canvas.mapTool()
        self.canvas.setMapTool(self._tool)
        self._message("Dra en ruta i kartan.")

    def _on_extent_drawn(self, rect: QgsRectangle) -> None:
        if rect.isEmpty():
            return
        self._set_area(rect, self.canvas.mapSettings().destinationCrs())
        self._restore_tool()

    def _on_tool_deactivated(self) -> None:
        self._previous_tool = None

    def _restore_tool(self) -> None:
        if self._previous_tool is not None:
            self.canvas.setMapTool(self._previous_tool)
        else:
            self.canvas.unsetMapTool(self._tool)

    # --- search ----------------------------------------------------------

    def _search_body(self) -> dict | None:
        if self.area is None:
            self._message("Välj ett område först.", Qgis.MessageLevel.Warning)
            return None
        a = self.area
        body: dict = {"bbox": [a.xMinimum(), a.yMinimum(), a.xMaximum(), a.yMaximum()]}
        service = SERVICES[self.service_combo.currentData()]
        if service.has_years:
            first, last = self.year_from.value(), self.year_to.value()
            if first > last:
                self._message("Första året är senare än sista året.", Qgis.MessageLevel.Warning)
                return None
            body["datetime"] = f"{first}-01-01T00:00:00Z/{last}-12-31T23:59:59Z"
        return body

    def _start_search(self) -> None:
        if self._search_task:
            return
        authcfg = self._authcfg_or_warn()
        body = self._search_body()
        if not authcfg or body is None:
            return
        self._save_settings()

        task = SearchTask(search_base_url(self.service_combo.currentData()), authcfg, body)
        task.status.connect(self.search_status.setText)
        task.completed.connect(self._on_search_completed)
        task.failed.connect(self._on_search_failed)
        task.taskTerminated.connect(self._clear_search)
        task.taskCompleted.connect(self._clear_search)
        self._search_task = task
        self.search_btn.setEnabled(False)
        QgsApplication.taskManager().addTask(task)

    def _clear_search(self) -> None:
        self._search_task = None
        self.search_btn.setEnabled(True)

    def _on_search_failed(self, error: str) -> None:
        self.search_status.setText("")
        self._message(error, Qgis.MessageLevel.Critical)

    def _on_search_completed(self, items: list, truncated: bool) -> None:
        self.items = items
        text = f"{len(items)} träffar."
        if truncated:
            text += f" Sökningen begränsades till {MAX_RESULTS}; snäva in området eller åren."
        self.search_status.setText(text)
        self._fill_results()
        self._show_footprints()

    # --- results ---------------------------------------------------------

    def _fill_results(self) -> None:
        self.tree.blockSignals(True)
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        for item in self.items:
            row = _SortableItem(
                [
                    item.id,
                    item.collection,
                    str(item.year or ""),
                    f"{item.resolution:g} m" if item.resolution else "",
                    _format_bytes(item.size),
                ]
            )
            row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            row.setCheckState(COL_NAME, Qt.CheckState.Unchecked)
            row.setData(COL_NAME, Qt.ItemDataRole.UserRole + 1, item)
            row.setData(COL_YEAR, Qt.ItemDataRole.UserRole, item.year or 0)
            row.setData(COL_RES, Qt.ItemDataRole.UserRole, item.resolution or 0)
            row.setData(COL_SIZE, Qt.ItemDataRole.UserRole, item.size or 0)
            self.tree.addTopLevelItem(row)
        self.tree.setSortingEnabled(True)
        self.tree.blockSignals(False)
        for column in range(5):
            self.tree.resizeColumnToContents(column)
        self._update_summary()

    def _checked_items(self) -> list[StacItem]:
        checked = []
        for i in range(self.tree.topLevelItemCount()):
            row = self.tree.topLevelItem(i)
            if row.checkState(COL_NAME) == Qt.CheckState.Checked:
                checked.append(row.data(COL_NAME, Qt.ItemDataRole.UserRole + 1))
        return checked

    def _set_all_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(COL_NAME, state)
        self.tree.blockSignals(False)
        self._update_summary()

    def _update_summary(self, *_args) -> None:
        checked = self._checked_items()
        known = sum(i.size for i in checked if i.size)
        unknown = sum(1 for i in checked if not i.size)
        text = f"{len(checked)} av {len(self.items)} valda, {_format_bytes(known)}"
        if unknown:
            text += f" (+{unknown} med okänd storlek)"
        self.summary_label.setText(text)

    def _show_footprints(self) -> None:
        """Show the hits as footprints in a temporary layer."""
        if self._footprints is not None:
            QgsProject.instance().removeMapLayer(self._footprints.id())
            self._footprints = None
        if not self.items:
            return
        layer = QgsVectorLayer(f"Polygon?crs={SEARCH_CRS}", FOOTPRINT_LAYER, "memory")
        provider = layer.dataProvider()
        provider.addAttributes(
            [
                QgsField("id", _STRING),
                QgsField("kollektion", _STRING),
                QgsField("ar", _INT),
                QgsField("upplosning", _DOUBLE),
                QgsField("storlek_mb", _DOUBLE),
            ]
        )
        layer.updateFields()
        features = []
        for item in self.items:
            feature = QgsFeature(layer.fields())
            feature.setGeometry(_item_geometry(item))
            feature.setAttributes(
                [
                    item.id,
                    item.collection,
                    item.year,
                    item.resolution,
                    round(item.size / 1024**2, 1) if item.size else None,
                ]
            )
            features.append(feature)
        provider.addFeatures(features)
        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)
        self._footprints = layer

    # --- download --------------------------------------------------------

    def _start_download(self) -> None:
        if self._queue:
            return
        authcfg = self._authcfg_or_warn()
        if not authcfg:
            return
        items = self._checked_items()
        if not items:
            self._message("Markera minst en ruta att hämta.", Qgis.MessageLevel.Warning)
            return
        output = self.output_widget.filePath()
        if not output:
            self._message("Välj en målmapp.", Qgis.MessageLevel.Warning)
            return

        total = sum(i.size for i in items if i.size)
        if total > WARN_BYTES:
            answer = QMessageBox.question(
                self,
                PLUGIN_NAME,
                f"Du är på väg att hämta {len(items)} filer, ungefär {_format_bytes(total)}. Fortsätta?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._save_settings()

        queue = DownloadQueue(items, authcfg, Path(output), self)
        queue.progress.connect(self._on_download_progress)
        queue.finished.connect(self._on_download_finished)
        self._queue = queue
        self.download_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        queue.start()

    def _cancel(self) -> None:
        if self._queue:
            self.progress_label.setText("Avbryter…")
            self._queue.cancel()

    def _on_download_progress(self, index: int, count: int, name: str, received: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 1000)
            self.progress.setValue(int(1000 * received / total))
        else:
            self.progress.setRange(0, 0)
        self.progress_label.setText(
            f"Fil {index} av {count}: {name} ({_format_bytes(received)} av {_format_bytes(total or None)})"
        )

    def _on_download_finished(self, paths: list, failures: list, cancelled: bool) -> None:
        queue, self._queue = self._queue, None
        if queue:
            queue.deleteLater()
        self.download_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        self.progress.setVisible(False)
        self.progress_label.setText("")

        if self.add_to_project.isChecked():
            for path in paths:
                layer = QgsRasterLayer(path, Path(path).stem)
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                else:
                    failures.append(f"{Path(path).name}: kunde inte öppnas som raster")

        if failures:
            self._message(
                f"{len(paths)} filer hämtade, {len(failures)} misslyckades: " + "; ".join(failures[:3]),
                Qgis.MessageLevel.Warning,
            )
        elif cancelled:
            self._message(f"Avbrutet. {len(paths)} filer hann hämtas.", Qgis.MessageLevel.Warning)
        else:
            self._message(f"{len(paths)} filer hämtade.", Qgis.MessageLevel.Success)


def _polygon_type():
    try:
        return Qgis.GeometryType.Polygon
    except AttributeError:  # QGIS < 3.30
        from qgis.core import QgsWkbTypes

        return QgsWkbTypes.PolygonGeometry


def _item_geometry(item: StacItem) -> QgsGeometry:
    if item.geometry:
        geometry = QgsGeometry.fromWkt(_geojson_to_wkt(item.geometry))
        if not geometry.isNull():
            return geometry
    return QgsGeometry.fromRect(QgsRectangle(*item.bbox))


def _geojson_to_wkt(geometry: dict) -> str:
    """WKT for the simple polygon geometries STAC items use here."""
    if geometry.get("type") != "Polygon":
        return ""
    rings = [
        "(" + ", ".join(f"{x} {y}" for x, y, *_ in ring) + ")"
        for ring in geometry.get("coordinates", [])
    ]
    return f"POLYGON({', '.join(rings)})"
