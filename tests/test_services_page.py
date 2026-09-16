import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICES_PAGE = PROJECT_ROOT / "src" / "pages" / "services.astro"


class ServicesPageLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SERVICES_PAGE.read_text(encoding="utf-8")

    def test_hero_spacing_uses_clamp_for_modern_flow(self):
        # Hero should use viewport-relative spacing instead of massive fixed padding
        self.assertIn("clamp(", self.source)
        # Should not use var(--space-20) which is too massive
        self.assertNotIn("var(--space-20)", self.source)

    def test_hero_has_visual_depth(self):
        # Hero or section backgrounds should use gradients for modern feel
        self.assertIn("radial-gradient(", self.source)

    def test_section_backgrounds_have_depth(self):
        # At least one section should use a gradient background
        gradient_count = self.source.count("radial-gradient(") + self.source.count("linear-gradient(")
        self.assertGreater(gradient_count, 2, "Need more gradient backgrounds for modern depth")

    def test_service_components_present(self):
        # Core service content must be present
        for marker in (
            "Weddings & Private Events",
            "Corporate Events",
            "Nightlife & Clubs",
            "Music Production",
            "Booking Process",
            "Service Area",
        ):
            self.assertIn(marker, self.source)

    def test_production_services_grid(self):
        # Production services should use a responsive grid
        self.assertIn("grid grid-3", self.source)

    def test_process_steps_grid(self):
        # 7-step booking process should use a multi-column grid
        self.assertIn("grid grid-4", self.source)
        self.assertIn("grid grid-2", self.source)  # smaller screens: 2 columns
        self.assertIn("1fr", self.source)  # smallest: 1 column

    def test_area_girds_stacked_on_mobile(self):
        # Service area should stack to 1fr on mobile screens
        self.assertRegex(
            self.source,
            r"@media\s*\(\s*max-width:\s*\d+px\s*\)[\s\S]*?grid-template-columns:\s*1fr",
        )

    def test_css_has_no_period_terminated_declarations(self):
        style_start = self.source.index("<style")
        style_end = self.source.index("</style>", style_start)
        css = self.source[style_start:style_end]
        malformed = re.findall(r"^\s*[a-zA-Z-]+:\s*[^;{}]+\.\s*$", css, re.MULTILINE)
        self.assertEqual(malformed, [], f"Malformed CSS declarations: {malformed[:5]}")

    def test_alternating_panels_with_modern_spacing(self):
        # Service detail panels should use clamp() for responsive spacing
        self.assertRegex(
            self.source,
            r"\.service-detail\s*\{[^}]*gap:\s*clamp\(",
        )
        # Panels should not use massive bottom margins
        self.assertNotIn("margin-bottom: var(--space-16)", self.source)

    def test_cta_section_modern_treatment(self):
        # CTA should be a panel with modern spacing
        self.assertIn("cta-panel", self.source)
        # CTA buttons should be in a flex row
        self.assertIn("cta-actions", self.source)


if __name__ == "__main__":
    unittest.main()
