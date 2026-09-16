import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = PROJECT_ROOT / "src" / "pages" / "index.astro"


class HomepageCollectionLimitsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOMEPAGE.read_text(encoding="utf-8")

    def test_homepage_uses_four_column_mix_grid(self):
        self.assertIn(
            '<div class="mixes-showcase grid grid-4" id="featured-mixes">',
            self.source,
        )

    def test_mix_cards_use_the_api_field_names(self):
        self.assertIn('data-mix="${mix.id}"', self.source)
        self.assertIn("mix.genre?.slice(0, 3)", self.source)

    def test_mix_card_media_host_is_scoped_to_its_renderer(self):
        renderer_start = self.source.index("function renderFeaturedMixes")
        renderer_end = self.source.index("function renderUpcomingGigs", renderer_start)
        renderer = self.source[renderer_start:renderer_end]
        self.assertIn(
            "const MediaHost = 'https://media.youknowmeasdubbz.com';",
            renderer,
        )
        self.assertIn("const coverSrc =", renderer)
        self.assertIn("mix.coverImage.startsWith('/')", renderer)

    def test_featured_mixes_have_distinct_valid_local_cover_art(self):
        from PIL import Image
        content_dir = PROJECT_ROOT / "src" / "content" / "mixes"
        cover_paths = []
        for filename in ("cultural-council-open-format.md", "avacado-saturday.md"):
            source = (content_dir / filename).read_text(encoding="utf-8")
            cover_line = next(line for line in source.splitlines() if line.startswith("coverImage:"))
            cover_path = cover_line.split('"', 2)[1]
            cover_paths.append(cover_path)
            image_path = PROJECT_ROOT / "public" / cover_path.lstrip("/")
            with Image.open(image_path) as image:
                image.load()
                self.assertEqual(image.size, (1200, 1200))
        self.assertEqual(len(set(cover_paths)), 2, "Featured mixes need distinct cover art")

    def test_all_white_party_is_replaced_by_uploaded_avacado_mix(self):
        content_dir = PROJECT_ROOT / "src" / "content" / "mixes"
        self.assertFalse((content_dir / "camelot-all-white.md").exists())
        avacado = (content_dir / "avacado-saturday.md").read_text(encoding="utf-8")
        self.assertIn("Avacado Cantina - Saturday Sessions", avacado)
        self.assertIn('/mixes/avacado-cantina-latin-2026.mp3', avacado)

    def test_homepage_renders_four_latest_mixes(self):
        self.assertIn("renderFeaturedMixes(mixes.slice(0, 4));", self.source)

    def test_homepage_renders_four_upcoming_events(self):
        self.assertIn(
            "const upcoming = gigs.filter(g => new Date(g.date) >= new Date()).slice(0, 4);",
            self.source,
        )

    def test_event_dates_are_parsed_as_local_calendar_dates(self):
        self.assertIn("const gigDate = new Date(`${gig.date}T00:00:00`);", self.source)
        self.assertIn("${gigDate.getDate()}", self.source)
        self.assertIn("gigDate.toLocaleDateString", self.source)


if __name__ == "__main__":
    unittest.main()
