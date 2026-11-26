# Changelog

- **Unreleased** (branch `seamlines`): Orthophoto search no longer shows the collection `orto-dsm-cog`. It is a paid surface model from aerial images, and the plugin only fetches data that is free of charge; the catalogue lists it among the orthophotos, but the download server refuses it (HTTP 403) without an agreement. The laser data collection `dsm-skoglig-copc` (Laserdata Skog) also has `dsm` in its name but is free (CC BY 4.0) and is included. New option *Hämta även metadatafil med sömlinjer (.json)* for orthophotos. It saves the metadata file of each tile, a GeoJSON with one polygon per aerial photo in the mosaic, with the photo id (`bildidentitet`) and the exact time (`tidpunkt`), as `<tile>_flygbild.json` next to the image. The file is always the whole tile's, also when only a clip of the image is downloaded, and in clip mode it is only fetched for tiles that are actually clipped. With *Lägg till i projektet när klart* it is added as a layer with unfilled yellow outlines and black labels. Works for historical orthophotos too.
- **1.1.2**: Elevation search now only covers `dtm-cog` (the ground model). Lantmäteriet's catalogue also lists `dsm-cog` (the paid surface model from aerial images), which cannot be downloaded without an agreement (HTTP 403) and is no longer shown. A refused download now reports the real reason instead of "kunde inte öppna filerna".
- **1.1.1**: Laser data (point clouds) is now always downloaded as whole files: the clip option and the PDAL dependency are removed for point clouds. Orthophoto and elevation clipping is unchanged. The result message after a laser data download now stays in the message bar until it is closed, and all errors are written to the QGIS log. COPC files are opened with QGIS' native COPC provider.
- **1.1.0**: New service *Laserdata (punktmoln)*: search the `dsm-skoglig-copc` point clouds on the map, see points and size per tile, and download them clipped to the drawn area with PDAL (or as whole COPC files). Licence CC BY 4.0. Tiles are now called "ruta" everywhere (2,5 km-ruta, 10 km-ruta), and 10 km tiles cut at the coast are marked "(beskuren)" instead of being shown as "5 km-ruta" or "10 km-blad".
- **1.0.7**: Moved the toolbar icon and menu entry from the Web toolbar/menu to the Plugins toolbar/menu; added the geodata tag.
- **1.0.6**: Clearer icon (bolder grid, smaller download arrow); shortened the changelog shown in the plugin manager, full history in CHANGELOG.md in the repository.
- **1.0.5**: QGIS 4 compatibility: raised qgisMaximumVersion to 4.99 and declared Qt6 support (supportsQt6=True); still works in QGIS 3.44+.
- **1.0.4**: Qt6 compatibility: use Qgis.GeometryType.Polygon directly instead of the removed QgsWkbTypes enum fallback.
- **1.0.3**: Silenced a false-positive Bandit warning (B105) on the public OAuth2 token endpoint URL.
- **1.0.2**: Dropped the self-hosted plugin-source install instructions - install from the release zip for now.
- **1.0.1**: Renamed to "Geodata: Ortofoto & höjd (Lantmäteriet)" with a new icon, part of a shared naming/icon scheme across the four Lantmäteriet plugins.
- **1.0.0**: First stable release (no longer marked experimental)
- **0.1.4**: Label dtm-cog sheets as 10 km tiles even when cut off at the coast
- **0.1.3**: Label elevation tiles by size and show when they were last changed
- **0.1.2**: Fix 401 error on large clips (path-specific GDAL auth) and keep colour and infrared tiles apart
- **0.1.1**: Renamed to Geodata Downloader (Lantmäteriet); state that the plugin is independent of Lantmäteriet
- **0.1.0**: First release: map-based search and download of orthophoto and elevation rasters, partial download of COG clips, build script and usage guide
