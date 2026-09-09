from django.template.loader import render_to_string
from django.test import SimpleTestCase

from main.models import HomePage


class HeroAccentTextTests(SimpleTestCase):
    def test_homepage_description_renders_marked_fragment_as_accent(self):
        page = HomePage(hero_description="Cel to **odŻYWIENIE**.")
        html = render_to_string("main/partials/hero.html", {"home_page": page})
        self.assertIn('<span class="content-accent">odŻYWIENIE</span>', html)
