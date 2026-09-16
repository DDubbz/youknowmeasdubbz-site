import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_LAYOUT = PROJECT_ROOT / "src" / "layouts" / "BaseLayout.astro"
LENIS_SCRIPT = PROJECT_ROOT / "src" / "scripts" / "lenis.js"


class BaseLayoutClientScriptTest(unittest.TestCase):
    def test_lenis_import_is_bundled_instead_of_emitted_inline(self):
        source = BASE_LAYOUT.read_text(encoding="utf-8")
        inline_initializer = "<script is:inline>\n      // Lenis smooth scroll init"
        self.assertNotIn(
            inline_initializer,
            source,
            "Module imports must be bundled by Astro, not emitted in a classic inline script",
        )
        self.assertIn('<script src="../scripts/lenis.js"></script>', source)
        self.assertIn(
            "import Lenis from '@studio-freight/lenis';",
            LENIS_SCRIPT.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
