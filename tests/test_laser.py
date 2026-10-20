"""Tests for the parts that run without QGIS: item parsing, services and PDAL pipelines.

Run from the repository root: python -m unittest discover tests
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lm_stac_downloader.config import SERVICES, search_base_url  # noqa: E402
from lm_stac_downloader.core.items import parse_item  # noqa: E402
from lm_stac_downloader.core.laser import (  # noqa: E402
    bounds_string,
    clip_path,
    clip_pipeline,
    find_pdal,
    merge_command,
    pipeline_json,
    tile_bounds,
    union_bounds,
)

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
    "assets": {"data": {"href": "https://dl1.example/x.tif", "type": "image/tiff; application=geotiff", "file:size": 10}},
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

    def test_raster_services_have_no_collection(self):
        self.assertIsNone(SERVICES["hojd"].collection)
        self.assertFalse(SERVICES["hojd"].point_cloud)


class PipelineTest(unittest.TestCase):
    def test_bounds_string(self):
        self.assertEqual(
            bounds_string((453000, 6395800, 453100, 6395900)),
            "([453000.000,453100.000],[6395800.000,6395900.000])",
        )

    def test_clip_pipeline(self):
        pipeline = clip_pipeline("https://host/a.copc.laz", "Bearer abc", (1, 2, 3, 4), "out.laz")
        reader, writer = pipeline["pipeline"]
        self.assertEqual(reader["type"], "readers.copc")
        self.assertEqual(reader["filename"], {"path": "https://host/a.copc.laz", "headers": {"Authorization": "Bearer abc"}})
        self.assertEqual(reader["bounds"], "([1.000,3.000],[2.000,4.000])")
        self.assertEqual(writer["type"], "writers.las")
        self.assertEqual(writer["compression"], "laszip")
        self.assertEqual(json.loads(pipeline_json(pipeline)), pipeline)

    def test_merge_command(self):
        self.assertEqual(merge_command("pdal", ["a.laz", "b.laz"], "out.laz"), ["pdal", "merge", "a.laz", "b.laz", "out.laz"])


class BoundsTest(unittest.TestCase):
    def setUp(self):
        self.item = parse_item(COPC_FEATURE, point_cloud=True)

    def test_inside(self):
        self.assertEqual(tile_bounds(self.item, (453000, 6395800, 453100, 6395900)), (453000, 6395800, 453100, 6395900))

    def test_clipped_to_tile(self):
        self.assertEqual(tile_bounds(self.item, (450000, 6390000, 453000, 6396000)), (452500, 6395000, 453000, 6396000))

    def test_outside(self):
        self.assertIsNone(tile_bounds(self.item, (460000, 6400000, 461000, 6401000)))

    def test_touching_edge_is_outside(self):
        self.assertIsNone(tile_bounds(self.item, (455000, 6395000, 456000, 6397500)))

    def test_union(self):
        self.assertEqual(union_bounds([(1, 2, 3, 4), (0, 3, 5, 6)]), (0, 2, 5, 6))

    def test_clip_path(self):
        path = clip_path(Path("out"), "dsm-skoglig-copc", (453000.2, 6395800.4, 453100.0, 6395900.0))
        self.assertEqual(path, Path("out/dsm-skoglig-copc/dsm-skoglig-copc_utsnitt_453000_6395800_453100_6395900.laz"))


class FindPdalTest(unittest.TestCase):
    def test_found_in_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = ("pdal.exe", "pdal")
            for name in names:
                (Path(tmp) / name).write_text("")
            found = find_pdal(["/does/not/exist", tmp], which=lambda _n: "/usr/bin/pdal")
            self.assertEqual(Path(found).parent, Path(tmp))

    def test_falls_back_to_path(self):
        self.assertEqual(find_pdal(["/does/not/exist"], which=lambda _n: "/usr/bin/pdal"), "/usr/bin/pdal")

    def test_missing(self):
        self.assertIsNone(find_pdal([], which=lambda _n: None))


if __name__ == "__main__":
    unittest.main()
