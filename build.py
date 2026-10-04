"""Build a distributable plugin zip and a QGIS plugin repository (plugins.xml).

    python build.py                     # zip + plugins.xml for GitHub Releases
    python build.py --base-url file:///S:/qgis-plugins

The zip holds only committed files (git archive), so commit before building.
Output: dist/lm_stac_downloader.<version>.zip and plugins.xml in the repo root.
"""

from __future__ import annotations

import argparse
import configparser
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN_DIR = "lm_stac_downloader"
ICON_URL = "https://raw.githubusercontent.com/matself/LM-STAC-Downloader/main/lm_stac_downloader/icon.png"
GITHUB_RELEASES = "https://github.com/matself/LM-STAC-Downloader/releases/download/v{version}"


def read_metadata() -> dict[str, str]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ROOT / PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    return dict(parser["general"])


def build_zip(version: str) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    # "<package>.<version>.zip": QGIS takes the plugin folder name from the file
    # name up to the first dot, so a dash here breaks installs from plugins.xml.
    zip_path = dist / f"{PLUGIN_DIR}.{version}.zip"
    subprocess.run(
        [
            "git", "archive", "--format=zip", f"--prefix={PLUGIN_DIR}/",
            f"HEAD:{PLUGIN_DIR}", "-o", str(zip_path),
        ],
        cwd=ROOT,
        check=True,
    )
    return zip_path


def build_plugins_xml(meta: dict[str, str], zip_name: str, base_url: str) -> Path:
    plugins = ET.Element("plugins")
    plugin = ET.SubElement(
        plugins, "pyqgis_plugin",
        name=meta["name"], version=meta["version"], plugin_id=PLUGIN_DIR,
    )
    fields = {
        "description": meta.get("description", ""),
        "about": meta.get("about", ""),
        "version": meta["version"],
        "qgis_minimum_version": meta.get("qgisminimumversion", ""),
        "qgis_maximum_version": meta.get("qgismaximumversion", ""),
        "supports_qt6": meta.get("supportsqt6", "False"),
        "homepage": meta.get("homepage", ""),
        "file_name": zip_name,
        "icon": ICON_URL,
        "author_name": meta.get("author", ""),
        "download_url": f"{base_url.rstrip('/')}/{zip_name}",
        "uploaded_by": meta.get("author", ""),
        "experimental": meta.get("experimental", "False"),
        "deprecated": meta.get("deprecated", "False"),
        "tracker": meta.get("tracker", ""),
        "repository": meta.get("repository", ""),
        "tags": meta.get("tags", ""),
    }
    for tag, text in fields.items():
        ET.SubElement(plugin, tag).text = text

    ET.indent(plugins)
    xml_path = ROOT / "plugins.xml"
    # Bytes, not text mode, so Windows doesn't turn newlines into CRLF.
    xml_path.write_bytes(ET.tostring(plugins, encoding="utf-8", xml_declaration=True) + b"\n")
    return xml_path


def main() -> None:
    meta = read_metadata()
    version = meta["version"]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base-url",
        default=GITHUB_RELEASES.format(version=version),
        help="where the zip will be published (default: the GitHub release for this version)",
    )
    args = parser.parse_args()

    zip_path = build_zip(version)
    xml_path = build_plugins_xml(meta, zip_path.name, args.base_url)
    print(f"{zip_path.relative_to(ROOT)}\n{xml_path.relative_to(ROOT)} -> {args.base_url}")


if __name__ == "__main__":
    main()
