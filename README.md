# LM-STAC Downloader

QGIS-plugin för att söka och hämta **rasterdata** från Lantmäteriets STAC-tjänster, med sökning direkt i kartan.

Rita en ruta i kartan, se vilka ortofoton eller höjdrutor som täcker den, markera de du vill ha och hämta dem. Rutorna
är stora (en ortofotoruta är cirka 640 MB), så pluginet kan också hämta **bara det utsnitt du valt** och slå ihop det till
en enda fil.

| Data | Tjänst |
|---|---|
| Ortofoto | `https://api.lantmateriet.se/stac-bild/v1` |
| Höjddata (markhöjdmodell) | `https://api.lantmateriet.se/stac-hojd/v1` |

Punktmoln, vektordata och NGP-kataloger ingår inte. För NGP, se [ngp-downloader](https://github.com/matself/ngp-downloader).

## Installera

Pluginet finns inte i det officiella plugin-repot. Lägg i stället till det här repot som plugin-källa i QGIS:

1. *Insticksprogram → Hantera och installera → Inställningar → Lägg till…*
2. URL: `https://raw.githubusercontent.com/matself/LM-STAC-Downloader/main/plugins.xml`
3. Kryssa i *Visa även experimentella insticksprogram* (pluginet är markerat experimentellt).
4. Sök efter *LM-STAC Downloader* och installera. Nya versioner visas sedan som vanliga uppdateringar.

Alternativt: hämta zip-filen under [Releases](https://github.com/matself/LM-STAC-Downloader/releases) och välj
*Installera från ZIP*.

Kräver **QGIS 3.44 eller senare** (OAuth 2-flödet Client Credentials).

## Kom igång

1. Skaffa åtkomstnycklar (Consumer Key och Consumer Secret) från Lantmäteriets API-manager, för ett systemkonto som har
   beställt *Ortofoto Nedladdning* och/eller *Markhöjdmodell Nedladdning* på Geotorget.
2. Öppna panelen via webbmenyn eller verktygsfältet. Klicka på *Ny Lantmäteriet-inloggning…* och ange nycklarna.
3. Välj tjänst, rita en ruta i kartan, sök, markera rutor och hämta.

Se **[användningsbeskrivningen](docs/anvandning.md)** för alla steg, hur utsnitt fungerar, och felsökning.

## Behörigheter

Sökning fungerar med alla giltiga nycklar, men nedladdning kräver att nycklarna hör till ett systemkonto som har beställt
*Ortofoto Nedladdning* respektive *Markhöjdmodell Nedladdning* (produktion) på Geotorget. Nycklar för Nationella
geodataplattformen (NGP-konsument) har inte den behörigheten i produktion. Pluginet lagrar inga inloggningsuppgifter,
utan använder QGIS autentiseringshanterare.

## Begränsningar

* Sökningen begränsas till 1000 träffar.
* Utsnittet följer området du sökte på, inte kartvyn vid hämtningstillfället.
* Höjdsökningen returnerar både `mhm-*` (rutor om 2,5 km, cirka 8 MB) och `dtm-cog` (10 km-blad, cirka 290 MB).
* Pluginet är testat mot QGIS 3.44 (Qt5). QGIS 4 / Qt6 är inte provat.

## Utveckling

Koden ligger i `lm_stac_downloader/`. Koppla in den i en QGIS-profil genom att länka eller kopiera mappen till profilens
`python/plugins`.

Ny version:

1. Höj `version` i `lm_stac_downloader/metadata.txt` och committa.
2. `python build.py` skapar `dist/lm_stac_downloader.<version>.zip` och uppdaterar `plugins.xml`.
3. Committa `plugins.xml`, pusha och skapa releasen:
   ```
   gh release create v<version> dist/lm_stac_downloader.<version>.zip --title "v<version>"
   ```

För en intern källa, till exempel en nätverksdisk: `python build.py --base-url file:///S:/qgis-plugins` och kopiera
zip-filen och `plugins.xml` dit.

## Licens

GPL-2.0-or-later, se [LICENSE](LICENSE).
