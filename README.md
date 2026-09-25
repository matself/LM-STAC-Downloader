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

## Användning

1. Öppna panelen via webbmenyn eller verktygsfältet.
2. Välj en autentisering (eller skapa en med Consumer Key/Consumer Secret).
3. Välj tjänst, och för ortofoto flygår. Välj område med "Använd kartvyn" eller "Rita ruta".
4. Sök. Träffarna visas i listan och som fotavtryck i ett tillfälligt lager.
5. Markera de rutor du vill ha, välj målmapp och hämta.

Filerna sparas som `<målmapp>/<kollektion>/<fil>.tif`. En hämtning som avbryts lämnar ingen ofullständig fil, och
redan hämtade filer av rätt storlek hoppas över.

## Status

Version 0.0.1. Sökning och nedladdning fungerar mot ortofoto (`stac-bild`) och höjddata (`stac-hojd`).

Kända begränsningar:

* En ortofotoruta är cirka 640 MB. Pluginet frågar innan det hämtar mer än 2 GB.
* Höjdsökningen returnerar både `mhm-*`-kollektionerna (rutor om cirka 8 MB) och `dtm-cog` (större filer). Hur de förhåller
  sig till varandra är inte utrett.
* Sökningen begränsas till 1000 träffar.
* Kräver QGIS 3.44 eller senare (Client Credentials-flödet).
