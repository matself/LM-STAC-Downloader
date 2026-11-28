"""Tests for how clip files are grouped and named, on saved items from the real API.

The fixture holds two historical tiles of the same ground flown in 1994 and 1999,
and two neighbouring tiles flown in 1957 and 1959.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lm_stac_downloader.core.items import parse_item  # noqa: E402
from lm_stac_downloader.core.mosaic import group_jobs, mosaic_path  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "historical_items.json"


class MosaicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        features = json.loads(FIXTURE.read_text(encoding="utf-8"))
        items = [parse_item(f) for f in features]
        # The clip area covers each whole tile.
        cls.jobs = {item.year: (item, item.proj_bbox) for item in items}

    def groups(self, *years):
        return group_jobs([self.jobs[year] for year in years])

    def test_years_covering_the_same_ground_get_one_file_each(self):
        groups = self.groups(1999, 1994)
        self.assertEqual([g.years for g in groups], ["1994", "1999"])
        self.assertEqual([len(g.members) for g in groups], [1, 1])

    def test_neighbouring_years_stay_in_one_file(self):
        (group,) = self.groups(1957, 1959)
        self.assertEqual((group.years, len(group.members)), ("1957-1959", 2))

    def test_collections_are_never_mixed(self):
        self.assertEqual([g.years for g in self.groups(1957, 1959, 1994, 1999)], ["1957-1959", "1994", "1999"])

    def test_only_the_clipped_parts_have_to_overlap(self):
        # The area misses the shared ground: the 1999 tile is only needed east of the 1994 one.
        item_94, (minx, miny, maxx, maxy) = self.jobs[1994]
        item_99 = self.jobs[1999][0]
        middle = (minx + maxx) / 2
        jobs = [(item_94, (minx, miny, middle, maxy)), (item_99, (middle, miny, maxx, maxy))]
        self.assertEqual([g.years for g in group_jobs(jobs)], ["1994-1999"])

    def test_file_name_tells_years_and_depends_on_the_tiles(self):
        (g94,), (g99,) = self.groups(1994), self.groups(1999)
        first, second = mosaic_path(Path("out"), g94), mosaic_path(Path("out"), g99)
        self.assertRegex(
            first.name, r"^orto-historiska-1990-1999_pan_1994_utsnitt_1550000_6365000_1555000_6370000_[0-9a-f]{8}\.tif$"
        )
        # Same area, other tiles: never the same file.
        self.assertNotEqual(first.name.rsplit("_", 1)[1], second.name.rsplit("_", 1)[1])

    def test_file_name_does_not_depend_on_the_order_of_the_tiles(self):
        (forward,), (backward,) = self.groups(1957, 1959), self.groups(1959, 1957)
        self.assertEqual(mosaic_path(Path("out"), forward), mosaic_path(Path("out"), backward))


if __name__ == "__main__":
    unittest.main()
