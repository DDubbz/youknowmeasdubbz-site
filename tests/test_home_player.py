import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = PROJECT_ROOT / "src" / "pages" / "index.astro"


class HomepagePlayerLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HOMEPAGE.read_text(encoding="utf-8")

    def test_controls_render_before_equalizer_so_animation_sits_below(self):
        player_start = self.__class__.source.index('<div class="hero-equalizer"')
        player_end = self.__class__.source.index('<script is:inline>', player_start)
        player_markup = self.__class__.source[player_start:player_end]

        controls_position = player_markup.index('class="player-controls"')
        bars_position = player_markup.index('class="equalizer-bars"')
        self.assertLess(
            controls_position,
            bars_position,
            "Player controls must be in normal flow above the decorative equalizer",
        )

    def test_controls_are_in_normal_flow_and_player_has_two_rows(self):
        # .hero-equalizer uses position: relative; .player-controls uses grid for layout
        hero_eq_rule = re.search(r"\.hero-equalizer\s*\{(?P<body>[^}]*)\}", self.__class__.source, re.S)
        if hero_eq_rule is None:
            self.fail("Missing .hero-equalizer rule")
        self.assertIn("position: relative", hero_eq_rule.group("body"))
        
        controls_rule = re.search(r"\.player-controls\s*\{(?P<body>[^}]*)\}", self.__class__.source, re.S)
        if controls_rule is None:
            self.fail("Missing .player-controls rule")
        self.assertIn("display: grid", controls_rule.group("body"))
        self.assertNotIn("position: absolute", controls_rule.group("body"))
        # Ensure equalizer-bars is a separate row below controls
        bars_rule = re.search(r"\.equalizer-bars\s*\{(?P<body>[^}]*)\}", self.__class__.source, re.S)
        if bars_rule is None:
            self.fail("Missing .equalizer-bars rule")
        self.assertIn("height:", bars_rule.group("body"))

    def test_play_button_uses_dedicated_player_styling(self):
        play_button = re.search(
            r'<button class="(?P<classes>[^"]*player-play-btn[^"]*)"[^>]*data-play-btn',
            self.__class__.source,
        )
        if play_button is None:
            self.fail("Missing player play button")
        classes = play_button.group("classes").split()
        self.assertNotIn("btn", classes, "Player button must not inherit large CTA padding")
        self.assertNotIn("btn-primary", classes, "Player button needs isolated dimensions")

    def test_player_keeps_real_audio_loading_and_visible_controls(self):
        self.assertIn("fetch('/api/mixes.json')", self.__class__.source)
        self.assertIn("https://media.youknowmeasdubbz.com", self.__class__.source)
        self.assertIn("data-play-btn", self.__class__.source)
        self.assertIn("data-volume-slider", self.__class__.source)
        self.assertIn("audio.play()", self.__class__.source)

    def test_player_uses_compact_timeline_group(self):
        self.assertIn('class="player-timeline"', self.__class__.source)
        self.assertIn('grid-template-areas:', self.__class__.source)

    def test_analyzer_has_no_separate_pause_control(self):
        self.assertNotIn('equalizer-toggle', self.__class__.source)
        self.assertNotIn('data-equalizer-toggle', self.__class__.source)


if __name__ == "__main__":
    unittest.main()