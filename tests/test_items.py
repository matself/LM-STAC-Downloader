"""Tests for the parts that run without QGIS: item parsing, services and tile labels.

Run from the repository root: python -m unittest discover tests
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lm_stac_downloader.config import SERVICES, search_base_url  # noqa: E402
from lm_stac_downloader.core.items import parse_item  # noqa: E402

COPC_FEATURE = {
    "id": "22b007-63950_4525_25",
    "collection": "dsm-skoglig-copc",
    "bbox": [14.2, 57.7, 14.3, 57.8],
    "geometry": None,
    "properties": {
        "datetime": "2021-06-01T00:00:00Z",
        "pc:count": 27_700_000,
        "proj:code": "EPSG:5845",
        "proj:bbox": [452500, 6395000, 455000, 6397500],
    },
    "assets": {
        "data": {
            "href": "https://dl1.lantmateriet.se/hojd/data/pointcloud/sls/22b007/y22b007-63950_4525_25.copc.laz",
            "type": "application/vnd.laszip+copc",
            "file:size": 156_623_062,
        }
    },
}

RASTER_FEATURE = {
    "id": "mhm-1",
    "collection": "mhm-2.5",
    "bbox": [14.2, 57.7, 14.3, 57.8],
    "properties": {"datetime": "2020-01-01T00:00:00Z", "upplosning": 1.0},
    "assets": {
        "data": {"href": "https://dl1.example/x.tif", "type": "image/tiff; application=geotiff", "file:size": 10}
    },
}


class ParseItemTest(unittest.TestCase):
    def test_point_cloud(self):
        item = parse_item(COPC_FEATURE, point_cloud=True)
        self.assertIsNotNone(item)
        self.assertTrue(item.point_cloud)
        self.assertEqual(item.points, 27_700_000)
        self.assertEqual(item.size, 156_623_062)
        self.assertEqual(item.crs, "EPSG:5845")
        self.assertEqual(item.year, 2021)
        self.assertEqual(item.kind, "2,5 km-ruta")
        self.assertEqual(item.filename, "y22b007-63950_4525_25.copc.laz")

    def test_raster_search_skips_point_clouds(self):
        self.assertIsNone(parse_item(COPC_FEATURE))

    def test_point_cloud_search_skips_rasters(self):
        self.assertIsNone(parse_item(RASTER_FEATURE, point_cloud=True))

    def test_raster_still_parses(self):
        item = parse_item(RASTER_FEATURE)
        self.assertIsNotNone(item)
        self.assertFalse(item.point_cloud)
        self.assertIsNone(item.points)

    def test_missing_or_bad_count(self):
        feature = json.loads(json.dumps(COPC_FEATURE))
        feature["properties"]["pc:count"] = None
        self.assertIsNone(parse_item(feature, point_cloud=True).points)


class ServiceTest(unittest.TestCase):
    def test_laser_service(self):
        service = SERVICES["laser"]
        self.assertTrue(service.point_cloud)
        self.assertEqual(service.collection, "dsm-skoglig-copc")
        self.assertEqual(search_base_url("laser"), "https://api.lantmateriet.se/stac-hojd/v1")

    def test_hojd_service_excludes_paid_surface_model(self):
        self.assertEqual(SERVICES["hojd"].collection, "dtm-cog")
        self.assertFalse(SERVICES["hojd"].point_cloud)
        self.assertIsNone(SERVICES["ortofoto"].collection)


def _item(item_id, proj_bbox, collection="dsm-skoglig-copc", point_cloud=True):
    from lm_stac_downloader.core.items import StacItem

    return StacItem(
        id=item_id, collection=collection, year=2025, resolution=None, size=None, href="https://x/y.laz",
        bbox=(), geometry=None, crs="EPSG:5845", proj_bbox=proj_bbox, point_cloud=point_cloud,
    )


class TileLabelTest(unittest.TestCase):
    def test_laser_tile_2_5_km(self):
        item = _item("25a002-61375_4400_25", (440000, 6137500, 442500, 6140000))
        self.assertEqual(item.tile_label, "2,5 km-ruta")

    def test_laser_tile_10_km_full(self):
        item = _item("22b007-639_45", (450000, 6390000, 460000, 6400000))
        self.assertEqual(item.tile_label, "10 km-ruta")

    def test_laser_tile_10_km_cut_is_not_called_5_km(self):
        item = _item("25a002-613_43", (435000, 6137500, 440000, 6140000))
        self.assertEqual(item.tile_label, "10 km-ruta (beskuren)")

    def test_dtm_cog_is_10_km(self):
        item = _item("613_44", (440000, 6135000, 450000, 6140000), collection="dtm-cog", point_cloud=False)
        self.assertEqual(item.tile_label, "10 km-ruta (beskuren)")

    def test_mhm_is_2_5_km(self):
        item = _item("x", (), collection="mhm-2.5", point_cloud=False)
        self.assertEqual(item.tile_label, "2,5 km-ruta")


if __name__ == "__main__":
    unittest.main()
