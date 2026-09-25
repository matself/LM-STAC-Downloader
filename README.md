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
5. Markera de rutor du vill ha, antingen i listan eller med "Välj rutor i kartan" (klicka på en ruta; där flera rutor
   överlappar väljer du i en meny).
6. Välj målmapp och hämta.

Filerna sparas som `<målmapp>/<kollektion>/<fil>.tif`. En hämtning som avbryts lämnar ingen ofullständig fil, och
redan hämtade filer av rätt storlek hoppas över.

### Hämta bara ett utsnitt

Rutorna är stora (en ortofotoruta är cirka 640 MB, ett höjdblad i `dtm-cog` cirka 290 MB). Filerna är Cloud Optimized
GeoTIFF, så med **"Hämta bara det valda området (utsnitt)"** hämtas bara de delar som täcker området du sökte på.
Utsnittet sparas som `<fil>_utsnitt_<koordinater>.tif` med samma koordinatsystem som originalet, och en utsnittsfil är
oftast några MB. Pluginet ger GDAL inloggningen från QGIS autentiseringshanterare, så ingen extra inloggning behövs.

## Behörigheter

Sökning fungerar med alla giltiga nycklar, men nedladdning kräver att nycklarna hör till ett systemkonto som har beställt
*Ortofoto Nedladdning* respektive *Markhöjdmodell Nedladdning* (produktion) på Geotorget. En NGP-konsument (t.ex.
NGP-nycklar) har inte den behörigheten i produktion. Se
[Åtkomstnycklar](https://qgissverige.github.io/lantmateriet-qgis-plugin/usage/installningar/atkomstnycklar/) i
`lantmateriet-qgis-plugin` för hur konton, applikationer och prenumerationer hänger ihop.

## Status

Version 0.0.1. Sökning, val av rutor i kartan, nedladdning och utsnitt fungerar mot ortofoto (`stac-bild`) och höjddata (`stac-hojd`).

Kända begränsningar:

* En ortofotoruta är cirka 640 MB. Pluginet frågar innan det hämtar mer än 2 GB.
* Höjdsökningen returnerar både `mhm-*`-kollektionerna (rutor om cirka 8 MB) och `dtm-cog` (större filer). Hur de förhåller
  sig till varandra är inte utrett.
* Sökningen begränsas till 1000 träffar.
* Utsnittet följer området du sökte på, inte kartvyn vid hämtningstillfället.
* Kräver QGIS 3.44 eller senare (Client Credentials-flödet).
