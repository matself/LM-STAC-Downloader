# Changelog

- **1.0.8**: Moved the toolbar icon and menu entry from the Web toolbar/menu to the Plugins toolbar/menu.
- **1.0.7**: Code style fixes (flake8), removed obsolete supportsQt6 key.
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
