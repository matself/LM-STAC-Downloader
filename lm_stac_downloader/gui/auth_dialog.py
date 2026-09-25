"""Dialog that creates a QGIS OAuth2 auth config preset for Lantmäteriet."""

from __future__ import annotations

from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from ..core.auth import create_client_credentials_config


class CreateAuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ny inloggning för Lantmäteriet")
        self.authcfg: str | None = None

        info = QLabel(
            "Skapar en OAuth2-konfiguration (client credentials) i QGIS "
            "autentiseringshanterare. Nyckel och hemlighet sparas krypterat av "
            "QGIS, inte av pluginet."
        )
        info.setWordWrap(True)

        self.name_edit = QLineEdit("Lantmäteriet STAC")
        self.client_id_edit = QLineEdit()
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Namn", self.name_edit)
        form.addRow("Consumer Key", self.client_id_edit)
        form.addRow("Consumer Secret", self.client_secret_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(info)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _create(self) -> None:
        client_id = self.client_id_edit.text().strip()
        client_secret = self.client_secret_edit.text().strip()
        if not client_id or not client_secret:
            QMessageBox.warning(
                self, self.windowTitle(), "Ange både Consumer Key och Consumer Secret."
            )
            return
        try:
            self.authcfg = create_client_credentials_config(
                self.name_edit.text().strip() or "Lantmäteriet STAC",
                client_id,
                client_secret,
            )
        except RuntimeError as e:
            QMessageBox.critical(self, self.windowTitle(), str(e))
            return
        self.accept()
