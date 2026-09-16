import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ABOUT_PAGE = PROJECT_ROOT / "src" / "pages" / "about.astro"
CONTACT_PAGE = PROJECT_ROOT / "src" / "pages" / "contact.astro"


class AboutPageLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ABOUT_PAGE.read_text(encoding="utf-8")

    def test_hero_uses_clamp_spacing(self):
        self.assertIn("clamp(", self.source)
        self.assertNotIn("var(--space-20)", self.source)

    def test_hero_has_visual_depth(self):
        self.assertIn("radial-gradient(", self.source)

    def test_bio_grid_is_responsive(self):
        self.assertIn("grid grid-2", self.source)

    def test_highlights_use_responsive_grid(self):
        self.assertIn("grid-template-columns: repeat(2, 1fr)", self.source)

    def test_approach_grid_uses_clamp_gap(self):
        self.assertRegex(self.source, r"\.approach-grid\s*\{[^}]*gap:\s*clamp\(")

    def test_approach_cards_have_hover(self):
        self.assertIn(".approach-card:hover", self.source)

    def test_roster_stacks_on_mobile(self):
        self.assertRegex(
            self.source,
            r"@media\s*\(\s*max-width:\s*768px\s*\)[\s\S]*?grid-template-columns:\s*1fr",
        )

    def test_dwbeatbeast_panel_exists(self):
        self.assertIn("dwbeatbeast-panel", self.source)

    def test_cta_section_modern(self):
        self.assertIn("cta-panel", self.source)
        self.assertIn("cta-actions", self.source)

    def test_css_has_no_period_terminated_declarations(self):
        style_start = self.source.index("<style")
        style_end = self.source.index("</style>", style_start)
        css = self.source[style_start:style_end]
        malformed = re.findall(r"^\s*[a-zA-Z-]+:\s*[^;{}]+\.\s*$", css, re.MULTILINE)
        self.assertEqual(malformed, [], f"Malformed CSS declarations: {malformed[:5]}")


class ContactPageLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CONTACT_PAGE.read_text(encoding="utf-8")

    def test_hero_uses_clamp_spacing(self):
        self.assertIn("clamp(", self.source)
        self.assertNotIn("var(--space-20)", self.source)

    def test_hero_has_visual_depth(self):
        self.assertIn("radial-gradient(", self.source)

    def test_contact_grid_is_responsive(self):
        self.assertIn("grid grid-2", self.source)

    def test_form_rows_stack_on_mobile(self):
        self.assertRegex(
            self.source,
            r"@media\s*\(\s*max-width:\s*640px\s*\)[\s\S]*?grid-template-columns:\s*1fr",
        )

    def test_faq_grid_responsive(self):
        self.assertIn("grid grid-2", self.source)

    def test_faq_stacks_on_mobile(self):
        self.assertRegex(
            self.source,
            r"@media\s*\(\s*max-width:\s*768px\s*\)[\s\S]*?grid-template-columns:\s*1fr",
        )

    def test_form_fields_have_focus_states(self):
        self.assertIn(":focus", self.source)

    def test_submit_button_full_width_on_mobile(self):
        self.assertIn("btn-full", self.source)

    def test_css_has_no_period_terminated_declarations(self):
        style_start = self.source.index("<style")
        style_end = self.source.index("</style>", style_start)
        css = self.source[style_start:style_end]
        malformed = re.findall(r"^\s*[a-zA-Z-]+:\s*[^;{}]+\.\s*$", css, re.MULTILINE)
        self.assertEqual(malformed, [], f"Malformed CSS declarations: {malformed[:5]}")


if __name__ == "__main__":
    unittest.main()