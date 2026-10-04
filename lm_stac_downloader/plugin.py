from __future__ import annotations

from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon

try:  # Qt6 / QGIS 4
    from qgis.PyQt.QtGui import QAction
except ImportError:  # Qt5 / QGIS 3
    from qgis.PyQt.QtWidgets import QAction

from .config import PLUGIN_NAME


class LmStacDownloaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action: QAction | None = None
        self.dock = None

    def initGui(self) -> None:
        icon = QIcon(str(Path(__file__).resolve().parent / "icon.svg"))
        self.action = QAction(icon, PLUGIN_NAME, self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.toggled.connect(self._toggle_dock)
        self.iface.addWebToolBarIcon(self.action)
        self.iface.addPluginToWebMenu(PLUGIN_NAME, self.action)

    def unload(self) -> None:
        if self.dock:
            self.dock.cleanup()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        if self.action:
            self.iface.removeWebToolBarIcon(self.action)
            self.iface.removePluginWebMenu(PLUGIN_NAME, self.action)
            self.action = None

    def _toggle_dock(self, checked: bool) -> None:
        if self.dock is None:
            from .gui.dock import StacDock

            self.dock = StacDock(self.iface, self.iface.mainWindow())
            self.dock.visibilityChanged.connect(self.action.setChecked)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.setVisible(checked)
