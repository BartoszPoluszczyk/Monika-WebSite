"""Regression checks for the sidebar photo and its independent layout rows."""
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class NavbarPhotoTests(unittest.TestCase):
    def test_photo_is_complete_and_decodes_to_the_last_row(self):
        path = ROOT / "static/images/navbar-food-bowl.png"
        with Image.open(path) as photo:
            photo.verify()  # Includes PNG chunk CRCs and the end-of-file marker.
        with Image.open(path) as photo:
            photo.load()  # A valid header alone is insufficient.
            self.assertEqual(photo.size, (1309, 1201))

    def test_caption_photo_and_button_have_independent_rows(self):
        css = (ROOT / "static/css/navigation.css").read_text()
        self.assertIn("grid-template-rows: auto minmax(140px, 1fr) auto", css)
        self.assertIn("line-height: 2.4", css)
        self.assertNotIn("clip-path: ellipse", css)
        photo_rule = css.split("    .navbar-footer-photo {", 1)[1].split("}", 1)[0]
        self.assertIn("object-fit: contain", photo_rule)
        self.assertIn("border-radius: 0", photo_rule)
        self.assertIn(".navbar-footer-photo { display: none; }", css)

    def test_updated_assets_have_new_cache_keys(self):
        templates = ROOT / "main/templates/main"
        self.assertIn("complete-20260910", (templates / "partials/navbar.html").read_text())
        base = (templates / "base.html").read_text()
        self.assertIn("navbar-photo-complete-20260910", base)
        self.assertIn("fonts/amsterdam-one.ttf", base)

if __name__ == "__main__":
    unittest.main()
