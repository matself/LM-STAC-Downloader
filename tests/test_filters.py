"""Tests for the orthophoto result filters, on saved items from the real API."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lm_stac_downloader.core import filters  # noqa: E402
from lm_stac_downloader.core.items import parse_item  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "ortho_items.json"


class FilterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        features = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.items = [parse_item(f) for f in features]
        cls.by_collection = {item.collection: item for item in cls.items}

    def selected(self, **selection):
        return {i.collection for i in self.items if filters.matches(i, selection)}

    def test_series(self):
        expected = {
            "orto-oskarshamn-2008": filters.TOWN,
            "orto-oskarshamn-2011": filters.TOWN,
            "orto-i2-2011": filters.AREA,
            "orto-b2-2026": filters.AREA,
            "orto-b2-2018": filters.AREA,
            "orto-historiska-1940-1959": filters.HISTORICAL,
        }
        self.assertEqual({c: filters.series(i) for c, i in self.by_collection.items()}, expected)

    def test_four_band_counts_as_colour_and_infrared(self):
        item = self.by_collection["orto-b2-2026"]
        self.assertEqual(filters.image_types(item), {filters.COLOUR, filters.INFRARED})

    def test_nothing_ticked_shows_everything(self):
        self.assertEqual(len(self.selected(resolution=set(), image_type=set(), series=set())), len(self.items))

    def test_ticks_in_one_group_add_up(self):
        one = self.selected(resolution={0.25})
        two = self.selected(resolution={0.25, 0.16})
        self.assertEqual(two, one | {"orto-b2-2026"})
        self.assertNotIn("orto-b2-2026", one)

    def test_groups_narrow_each_other(self):
        self.assertEqual(
            self.selected(resolution={0.25}, image_type={filters.INFRARED}),
            {"orto-oskarshamn-2011", "orto-b2-2018"},
        )

    def test_nothing_is_shown_above_the_limit(self):
        self.assertEqual(filters.select(self.items, {}, len(self.items) - 1), ([], len(self.items)))
        self.assertEqual(filters.select(self.items, {}, len(self.items)), (self.items, len(self.items)))

    def test_filters_bring_the_hits_under_the_limit(self):
        shown, count = filters.select(self.items, {filters.RESOLUTION: {0.16}}, 1)
        self.assertEqual(([i.collection for i in shown], count), (["orto-b2-2026"], 1))

    def test_available_options(self):
        self.assertEqual(filters.available(self.items, filters.RESOLUTION), {0.16, 0.25, 0.5})
        self.assertEqual(
            filters.available(self.items, filters.SERIES), {filters.AREA, filters.TOWN, filters.HISTORICAL}
        )


if __name__ == "__main__":
    unittest.main()
