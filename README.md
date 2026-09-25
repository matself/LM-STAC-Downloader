# LM-STAC Downloader

QGIS-plugin för att söka och hämta **rasterdata** från Lantmäteriets STAC-tjänster, med sökning direkt i kartan.

Första versionen omfattar:

| Data | Tjänst | Kollektion |
|---|---|---|
| Ortofoto | `https://api.lantmateriet.se/stac-bild/v1` | _(att fastställa)_ |
| Höjddata (markhöjdmodell) | `https://api.lantmateriet.se/stac-hojd/v1` | `dtm-cog` |

Autentisering sker via QGIS autentiseringshanterare (OAuth2 Client Credentials, Consumer Key/Consumer Secret från
Lantmäteriets API-manager). Pluginet lagrar inga inloggningsuppgifter.

Punktmoln, vektordata och NGP-kataloger ingår inte. För NGP, se [ngp-downloader](https://github.com/matself/ngp-downloader).

## Status

Tidigt skelett. Ingen funktionalitet ännu.
