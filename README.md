<img src="lm_stac_downloader/icon.svg" alt="" width="72" align="right">

# Geodata: Ortofoto & höjd (Lantmäteriet)

A QGIS plugin for searching and downloading **raster data and laser data (point clouds)** from Lantmäteriet's (the Swedish mapping,
cadastral and land registration authority) STAC services, with map-based search.

> **Independent plugin.** This plugin is not developed, reviewed or supported by Lantmäteriet. The name
> Lantmäteriet is used only to state which services the plugin works against. Questions about the plugin
> belong in [this repository's issues](https://github.com/matself/LM-STAC-Downloader/issues), not with
> Lantmäteriet's support. Data is fetched from Lantmäteriet's services and is subject to their terms of use.

Draw a box on the map, see which orthophoto, elevation or laser data tiles cover it, select the ones you want and
download them. The tiles are large (an orthophoto tile is roughly 640 MB), so the plugin can also download
**only the clip you selected** and mosaic it into a single file (orthophotos and elevation data). Laser data
(point clouds) is always downloaded as whole files, one file per tile.

Covers Sweden only: it queries Lantmäteriet's Swedish STAC services and requires access keys for a system
account ordered through Lantmäteriet's Geotorget (see [Permissions](#permissions)).

| Data | Service |
|---|---|
| Orthophoto | `https://api.lantmateriet.se/stac-bild/v1` |
| Elevation data (digital terrain model) | `https://api.lantmateriet.se/stac-hojd/v1` |
| Laser data (point clouds), collection `dsm-skoglig-copc` ("Laserdata Skog") | `https://api.lantmateriet.se/stac-hojd/v1` |

The plugin only fetches data that is free of charge. Lantmäteriet's catalogues also list paid products, for example the surface models (`dsm-cog` and `orto-dsm-cog`); these are left out of the search results. The laser data collection `dsm-skoglig-copc` ("Laserdata Skog") also has `dsm` in its name but is free (CC BY 4.0), and is included.

Laser data is licensed CC BY 4.0: credit Lantmäteriet as the source when you use it. Vector data and NGP catalogues are not included. For NGP, see
[ngp-downloader](https://github.com/matself/ngp-downloader).

## Install

Download the zip from [Releases](https://github.com/matself/LM-STAC-Downloader/releases) and
use *Plugins → Manage and Install Plugins → Install from ZIP*.

Requires **QGIS 3.44 or later** (the OAuth2 Client Credentials flow).

## Getting started

1. Get access keys (Consumer Key and Consumer Secret) from Lantmäteriet's API manager, for a system account
   that has ordered *Ortofoto Nedladdning* and/or *Markhöjdmodell Nedladdning* on Geotorget.
2. Open the panel from the web menu or the toolbar. Click *New Lantmäteriet login…* and enter the keys.
3. Pick a service, draw a box on the map, search, select tiles and download.

The user interface is in Swedish; the [User interface](#user-interface) section below explains every
dialog and label in English. For the full walkthrough (in Swedish), including how clipping works and
troubleshooting, see **[docs/anvandning.md](docs/anvandning.md)**.

## User interface

The plugin's user interface (labels, buttons and messages) is in Swedish. This section explains it in
English so the plugin can be reviewed and tested without knowing Swedish.

### Main dock panel

Opened from the web menu or the web toolbar (button *Geodata: Ortofoto & höjd (Lantmäteriet)*). It has three
groups: *Anslutning* (connection), *Sökning* (search) and, once there are hits, *Träffar* (hits) and
*Hämta* (download).

| Swedish label | English meaning | What it does |
|---|---|---|
| Anslutning | Connection | Group with the login button |
| Ny Lantmäteriet-inloggning… | New Lantmäteriet login… | Opens the login dialog (see below) |
| Sökning | Search | Group with the search controls |
| Tjänst | Service | Picks the data: *Ortofoto* (orthophoto), *Höjddata (markhöjdmodell)* (elevation) or *Laserdata (punktmoln)* (laser data, point clouds) |
| Flygår | Aerial survey year | Year filter for orthophoto search (hidden for elevation and laser data) |
| Använd kartvyn | Use map view | Uses the current map extent as the search area |
| Rita ruta | Draw box | Lets you draw a rectangle on the map as the search area |
| Inget område valt | No area selected | Shown until a search area has been set |
| Sök | Search | Runs the STAC search for the selected area and service |
| Rensa sökområde och träffar | Clear search area and hits | Removes the search box and the blue/orange result boxes from the map |
| Träffar | Hits | Group listing the search results (name, collection, type, year, resolution, changed, size) |
| Ruta, Kollektion, Typ, År, Upplösning, Ändrad, Storlek | Tile, Collection, Type, Year, Resolution, Changed, Size | Columns of the hit list. *Typ* is the image type for orthophotos (`rgb` colour, `cir` colour infrared, `pan` panchromatic) and the tile size for elevation and laser data |
| 2,5 km-ruta | 2.5 km tile | Value in *Typ*: a tile of 2.5 x 2.5 km |
| 10 km-ruta | 10 km tile | Value in *Typ*: a tile of 10 x 10 km |
| 10 km-ruta (beskuren) | 10 km tile (cut) | Value in *Typ*: a 10 km tile that is smaller than 10 x 10 km because it is cut to the land that exists, for example at the coast |
| Skannat | Scanned | Column replacing *År* (year) for laser data: the year of the scan |
| Punkter | Points | Column replacing *Upplösning* (resolution) for laser data: number of points in the tile, e.g. "27,7 milj." (27.7 million). The summary under the list adds up the points of the selected tiles |
| Välj rutor i kartan | Pick tiles on the map | Toggle: click a tile on the map to select or deselect it |
| Markera alla | Select all | Selects every hit |
| Avmarkera alla | Deselect all | Deselects every hit |
| Hämta | Download | Group with the download controls |
| Hämta bara det valda området (utsnitt) | Download only the selected area (clip) | If checked, only the drawn area is downloaded and mosaicked instead of the full tiles. Not shown for laser data, which is always downloaded as whole files |
| Laserdata: © Lantmäteriet, licens CC BY 4.0. Ange Lantmäteriet som källa när du använder datat. | Laser data: © Lantmäteriet, licence CC BY 4.0. Credit Lantmäteriet as the source when you use the data. | Attribution notice shown in the *Hämta* group for laser data |
| Hämta även metadatafil med sömlinjer (.json) | Also download the metadata file with seamlines (.json) | Orthophotos only. Saves the tile's metadata file, `<tile>_flygbild.json`, next to the image: a GeoJSON with one polygon per aerial photo in the mosaic, with the photo id and the exact time. The file is always the whole tile's, never clipped to the area, and is fetched after the images. Tiles without a metadata file are reported in the result message |
| Lägg till i projektet när klart | Add to project when done | Adds the downloaded raster(s) or point cloud(s) to the QGIS project once finished. Seamline files are added as layers with unfilled yellow outlines and black labels (photo id and date) |
| Hämta valda | Download selected | Starts downloading the selected hits |
| Avbryt | Cancel | Cancels an ongoing download |
| Fristående plugin, inte utvecklat av Lantmäteriet. | Independent plugin, not developed by Lantmäteriet. | Disclaimer label shown in the panel |

### Login dialog ("Ny inloggning för Lantmäteriet" / New Lantmäteriet login)

Opened by *Ny Lantmäteriet-inloggning…*. Creates an OAuth2 (client credentials) authentication
configuration in QGIS' own authentication manager; the key and secret are stored encrypted by QGIS, not
by the plugin.

| Swedish label | English meaning | What it does |
|---|---|---|
| Namn | Name | Name of the QGIS authentication configuration (defaults to "Lantmäteriet STAC") |
| Consumer Key | Consumer Key | The OAuth2 client id from Lantmäteriet's API manager |
| Consumer Secret | Consumer Secret | The OAuth2 client secret from Lantmäteriet's API manager |

### Messages

| Swedish message | English meaning | When it appears |
|---|---|---|
| Inget område valt | No area selected | No search area has been set yet |
| Ange både Consumer Key och Consumer Secret. | Enter both Consumer Key and Consumer Secret. | One of the two login fields is empty |
| Utsnitt {n} av {N}: {namn} ({procent} %) | Clip {n} of {N}: {name} ({percent}%) | Progress while clipping/downloading |
| Avbryter… | Cancelling… | Shown while a download is being cancelled |
| {n} filer hämtade. / {n} filer hämtade, {m} misslyckades: … / Avbrutet. {n} filer hann hämtas. | {n} files downloaded. / {n} files downloaded, {m} failed: … / Cancelled. {n} files were downloaded. | When a download ends. For laser data the message stays in the message bar until it is closed, and the full list of errors is written to the QGIS log |
| {n} valda rutor ligger utanför området och hoppas över. | {n} selected tiles are outside the area and are skipped. | Some selected tiles do not overlap the searched area |
| åtkomst nekad. Sökningen fungerade, men den valda autentiseringen får inte hämta filer. … | Access denied. The search worked, but the selected credentials are not allowed to download files. Check that the keys belong to a system account that has ordered *Ortofoto Nedladdning* or *Markhöjdmodell Nedladdning* (production) on Geotorget, and that the application subscribes to STAC-bild and/or STAC-hojd. | The download host returns HTTP 403 (Forbidden) |

## Permissions

Search works with any valid keys, but downloading requires that the keys belong to a system account that
has ordered *Ortofoto Nedladdning* and *Markhöjdmodell Nedladdning* (production) on Geotorget respectively.
Keys for Nationella geodataplattformen (NGP consumer) do not have that permission in production. The plugin
does not store any credentials itself; it uses QGIS' authentication manager.

## Limitations

* Search is limited to 1000 hits.
* The clip follows the area you searched on, not the map view at download time.
* Laser data: only the collection `dsm-skoglig-copc` is searched, and it does not cover all of Sweden. The files are
  COPC point clouds (about 100 to 160 MB per 2.5 km tile) in the file's own CRS (EPSG:5845), downloaded as whole files.
  There is no clipping for point clouds; cut out an area with your own tools (for example PDAL or QGIS processing).
  Lantmäteriet has said that the older 10 km tiles are being withdrawn (planned 2 November 2026) in favour of the 2.5 km tiles.
* Orthophoto search leaves out the collection `orto-dsm-cog`: it is a paid surface model from aerial images, and the plugin only fetches free data. The catalogue lists it among the orthophotos, but the download server refuses it (HTTP 403) without an agreement.
* Elevation search covers `dtm-cog` only (mostly 10 km tiles of roughly 350 MB; the 2.5 km `mhm-2.5` collection is no longer in the catalogue). The paid surface model `dsm-cog` is deliberately left out: the catalogue lists it, but downloads are refused (HTTP 403) without an agreement.
* The plugin is tested with QGIS 4.2.3 (Qt6, Windows). QGIS 3.44 (Qt5) was tested for orthophotos and elevation data in
  earlier versions; laser data has not been tested there or on Linux/macOS.

## Development

Unit tests that run without QGIS: `python -m unittest discover tests`.

The code lives in `lm_stac_downloader/`. Hook it into a QGIS profile by linking or copying the folder into
the profile's `python/plugins`.

New version:

1. Bump `version` in `lm_stac_downloader/metadata.txt` and commit.
2. `python build.py` creates `dist/lm_stac_downloader.<version>.zip` and updates `plugins.xml`.
3. Commit `plugins.xml`, push and create the release:
   ```
   gh release create v<version> dist/lm_stac_downloader.<version>.zip --title "v<version>"
   ```

For an internal source, for example a network drive: `python build.py --base-url file:///S:/qgis-plugins`
and copy the zip file and `plugins.xml` there.

## License

GPL-2.0-or-later, see [LICENSE](LICENSE).
