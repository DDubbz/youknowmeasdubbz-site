import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIXES_PAGE = PROJECT_ROOT / "src" / "pages" / "mixes.astro"


class MixesPageLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MIXES_PAGE.read_text(encoding="utf-8")

    def test_dynamic_playlist_styles_are_global(self):
        self.assertIn("<style is:global>", self.source)
        self.assertIn(".playlist-track", self.source)
        self.assertIn(".playlist-track-cover img", self.source)

    def test_modern_player_structure_is_present(self):
        for marker in (
            'class="mixes-studio"',
            'class="player-artwork"',
            'class="player-timeline"',
            'class="playlist-toolbar"',
            'class="playlist-count"',
            'class="mixes-hero-meta"',
        ):
            self.assertIn(marker, self.source)
        self.assertIn("data-player-artwork", self.source)
        self.assertIn("data-audio", self.source)

    def test_analyzer_runs_without_separate_pause_button(self):
        self.assertNotIn("data-equalizer-toggle", self.source)
        self.assertNotIn("equalizer-toggle", self.source)
        self.assertNotIn("eqToggle", self.source)
        self.assertIn("data-equalizer-bars", self.source)

    def test_existing_player_features_remain(self):
        for hook in (
            "data-shuffle-btn",
            "data-repeat-btn",
            "data-mute-btn",
            "data-volume-slider",
            "data-progress-bar",
            "touchmove",
            "localStorage",
            "URLSearchParams",
            "case 's':",
            "case 'r':",
            "case 'm':",
        ):
            self.assertIn(hook, self.source)

    def test_player_artwork_pans_smoothly_without_ignoring_reduced_motion(self):
        self.assertIn("@keyframes artwork-pan", self.source)
        self.assertRegex(
            self.source,
            r"\.player-artwork-image\s*\{[^}]*animation:\s*artwork-pan",
        )
        self.assertIn("prefers-reduced-motion: reduce", self.source)
        self.assertRegex(
            self.source,
            r"prefers-reduced-motion:\s*reduce[\s\S]*?\.player-artwork-image\s*\{[^}]*animation:\s*none",
        )

    def test_previous_and_next_mix_controls_are_wired(self):
        for hook in (
            "data-previous-btn",
            "data-next-btn",
            "const previousBtn =",
            "const nextBtn =",
            "function skipTrack(direction)",
            "previousBtn?.addEventListener",
            "nextBtn?.addEventListener",
        ):
            self.assertIn(hook, self.source)

    def test_local_cover_art_is_used_when_available(self):
        self.assertIn("const coverSrc =", self.source)
        self.assertIn("mix.coverImage.startsWith('/')", self.source)
        self.assertIn("coverSrc(mix)", self.source)

    def test_css_has_no_period_terminated_declarations(self):
        style_start = self.source.index("<style")
        style_end = self.source.index("</style>", style_start)
        css = self.source[style_start:style_end]
        malformed = re.findall(r"^\s*[a-zA-Z-]+:\s*[^;{}]+\.\s*$", css, re.MULTILINE)
        self.assertEqual(malformed, [], f"Malformed CSS declarations: {malformed[:5]}")


if __name__ == "__main__":
    unittest.main()
