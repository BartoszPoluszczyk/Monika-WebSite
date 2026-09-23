from pathlib import Path

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class NavigationScrollSpyTests(SimpleTestCase):
    section_ids = (
        "strona-glowna",
        "o-mnie",
        "pomoc",
        "oferta",
        "wspolpraca",
        "opinie",
    )

    def test_navigation_links_declare_scrollspy_targets(self):
        html = render_to_string("main/partials/navbar.html")

        for section_id in self.section_ids:
            with self.subTest(section_id=section_id):
                self.assertIn(
                    f'data-scrollspy-target="{section_id}"',
                    html,
                )

    def test_hero_has_home_section_identifier(self):
        html = render_to_string("main/partials/hero.html")

        self.assertIn(
            '<section class="hero" id="strona-glowna">',
            html,
        )

    def test_navigation_script_tracks_scroll_without_rewriting_history(self):
        script_path = finders.find("js/navigation.js")
        self.assertIsNotNone(script_path)
        script = Path(script_path).read_text(encoding="utf-8")

        for fragment in (
            "dataset.scrollspyTarget",
            "updateActiveFromScroll",
            'window.addEventListener("scroll"',
            "window.requestAnimationFrame",
            'link.classList.toggle("is-active", active)',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, script)

        self.assertNotIn("history.pushState", script)
        self.assertNotIn("history.replaceState", script)
