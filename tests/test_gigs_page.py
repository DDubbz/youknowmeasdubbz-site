import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GIGS_PAGE = PROJECT_ROOT / "src" / "pages" / "gigs.astro"


class GigsPageLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GIGS_PAGE.read_text(encoding="utf-8")

    def test_modern_gig_card_structure(self):
        for marker in (
            "gig-card",
            "gig-date",
            "gig-info",
            "gig-venue",
            "gig-status",
            "gig-filters",
            "filter-btn",
            "gigs-list",
            "load-more-gigs",
        ):
            self.assertIn(marker, self.source)

    def test_gig_card_has_modern_panel_treatment(self):
        # Each gig card should look like a card, not floating text
        self.assertIn("padding:", self.source)
        self.assertIn("border:", self.source)

    def test_status_badges_are_prominent(self):
        # Status badges should be visible and color-coded
        self.assertIn("gig-status.booked", self.source)
        self.assertIn("gig-status.actual", self.source)
        self.assertIn("gig-status.expected", self.source)

    def test_residency_cards_are_modern(self):
        self.assertIn("residency-card", self.source)
        self.assertIn("residency-icon", self.source)

    def test_filters_wrap_cleanly_on_mobile(self):
        # Filter bar should have flex-wrap: nowrap in base styles (scrollable on mobile)
        self.assertRegex(
            self.source,
            r"\.gig-filters\s*\{[^}]*flex-wrap:\s*nowrap",
        )
        # Filter buttons should be non-shrinking and horizontally scrollable
        self.assertIn("overflow-x: auto", self.source)
        self.assertIn("flex: 0 0 auto", self.source)

    def test_mobile_residency_cards_stacked(self):
        self.assertRegex(
            self.source,
            r"@media\s*\(\s*max-width:\s*768px\s*\)[\s\S]*?\.residencies-grid\s*\{[^}]*grid-template-columns:\s*1fr",
        )

    def test_css_has_no_period_terminated_declarations(self):
        style_start = self.source.index("<style")
        style_end = self.source.index("</style>", style_start)
        css = self.source[style_start:style_end]
        malformed = re.findall(r"^\s*[a-zA-Z-]+:\s*[^;{}]+\.\s*$", css, re.MULTILINE)
        self.assertEqual(malformed, [], f"Malformed CSS declarations: {malformed[:5]}")

    def test_gig_card_uses_grid_layout(self):
        # Cards should use grid for date | info | status layout
        self.assertIn("grid-template-columns", self.source)


if __name__ == "__main__":
    unittest.main()
