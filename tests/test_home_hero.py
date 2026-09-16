import unittest
import urllib.request
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = PROJECT_ROOT / 'src' / 'pages' / 'index.astro'

class HeroParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.images = []
        self.links = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and attrs.get('aria-labelledby') == 'hero-title':
            self.inside = True
        if self.inside and tag == 'img':
            self.images.append(attrs)
        if self.inside and tag == 'a':
            self.links.append(attrs.get('href'))
    def handle_endtag(self, tag):
        if tag == 'section':
            self.inside = False
    def handle_data(self, data):
        if self.inside:
            self.text.append(data)

class HomepageHeroTest(unittest.TestCase):
    def test_homepage_css_has_no_period_terminated_declarations(self):
        import re
        source = HOMEPAGE.read_text(encoding='utf-8')
        malformed = re.findall(r'^\s+[a-zA-Z-]+:\s*[^;{}]+\.\s*$', source, re.MULTILINE)
        self.assertEqual(malformed, [], 'CSS declarations must end with semicolons, not periods')

    def test_hero_and_homepage_have_modern_flow_structure(self):
        source = HOMEPAGE.read_text(encoding='utf-8')
        self.assertIn('class="hero-meta"', source)
        self.assertIn('class="player-timeline"', source)
        self.assertGreaterEqual(source.count('class="section-kicker"'), 4)
        self.assertIn('home-section-mixes', source)
        self.assertIn('home-section-gigs', source)

    def test_brand_styles_are_delivered(self):
        import re
        html = urllib.request.urlopen('http://localhost:4321/').read().decode()
        styles = re.findall(r'href="([^\"]+\.css)"', html)
        css = html + ''.join(
            urllib.request.urlopen(urljoin('http://localhost:4321/', url)).read().decode()
            for url in styles
        )
        self.assertIn('--font-display:', css, 'Brand typography stylesheet must be loaded')

    def test_hero_typography_and_equalizer(self):
        html = urllib.request.urlopen('http://localhost:4321/').read().decode()
        self.assertIn('hero-name-intro', html)
        self.assertIn('You Know Me As</span>', html)
        self.assertIn('hero-name-main', html)
        self.assertIn('hero-equalizer', html)

    def test_approved_photo_hero_is_served(self):
        parser = HeroParser()
        parser.feed(urllib.request.urlopen('http://localhost:4321/').read().decode())
        self.assertEqual(len(parser.images), 1, 'Hero must render the supplied photograph')
        image = parser.images[0]
        self.assertTrue(image['src'].endswith('.webp'))
        self.assertEqual(image.get('fetchpriority'), 'high')
        self.assertTrue(image.get('alt'))
        response = urllib.request.urlopen(urljoin('http://localhost:4321/', image['src']))
        self.assertEqual(response.headers.get_content_type(), 'image/webp')
        self.assertEqual(response.read(4), b'RIFF')
        text = ' '.join(parser.text)
        self.assertIn('Open-format DJ sets', text)
        self.assertNotIn('1000+', text)
        self.assertNotIn('most requested', text)
        self.assertIn('/contact', parser.links)
        self.assertIn('/mixes', parser.links)

if __name__ == '__main__':
    unittest.main()
