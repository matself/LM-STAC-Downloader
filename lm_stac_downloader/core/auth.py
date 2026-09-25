"""Helpers around QGIS' built-in authentication manager.

The plugin never stores credentials itself. It only keeps the id of a QGIS
authentication configuration (authcfg); secrets live in QGIS' encrypted
auth database and tokens are fetched/refreshed by QGIS' OAuth2 method.
"""

from __future__ import annotations

import json

from qgis.core import QgsApplication, QgsAuthMethodConfig

from ..config import TOKEN_URL

# Values from QgsAuthOAuth2Config (not exposed to Python).
_GRANT_FLOW_CLIENT_CREDENTIALS = 4
_CONFIG_TYPE_CUSTOM = 1
_ACCESS_METHOD_HEADER = 0


def create_client_credentials_config(name: str, client_id: str, client_secret: str) -> str:
    """Create an OAuth2 (client credentials) auth config for Lantmäteriet.

    Returns the new authcfg id. Raises RuntimeError if the config could not
    be stored (e.g. the user cancelled the master password prompt).
    """
    auth_manager = QgsApplication.authManager()
    if not auth_manager.setMasterPassword(True):
        raise RuntimeError("QGIS huvudlösenord krävs för att spara autentiseringen.")

    oauth2 = {
        "version": 1,
        "configType": _CONFIG_TYPE_CUSTOM,
        "grantFlow": _GRANT_FLOW_CLIENT_CREDENTIALS,
        "name": name,
        "tokenUrl": TOKEN_URL,
        "clientId": client_id,
        "clientSecret": client_secret,
        "accessMethod": _ACCESS_METHOD_HEADER,
        "persistToken": False,
        "requestTimeout": 30,
    }

    config = QgsAuthMethodConfig("OAuth2")
    config.setName(name)
    config.setConfig("oauth2config", json.dumps(oauth2))

    result = auth_manager.storeAuthenticationConfig(config)
    # SIP_INOUT: some QGIS versions return (bool, config), others just bool.
    if isinstance(result, tuple):
        ok, config = result
    else:
        ok = result
    if not ok or not config.id():
        raise RuntimeError("Kunde inte spara autentiseringskonfigurationen.")
    return config.id()


def authcfg_exists(authcfg: str) -> bool:
    return bool(authcfg) and authcfg in QgsApplication.authManager().configIds()
