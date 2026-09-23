from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class HomeSectionFlowStylesTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.styles = (Path(settings.BASE_DIR) / "static/css/style.css").read_text(
            encoding="utf-8"
        )

    def test_home_sections_have_no_outer_vertical_spacing(self):
        continuity_styles = self.styles.split(
            "/* Strona glowna: sekcje lacza sie bez bialych szczelin", 1
        )[1]

        for selector in (
            ".site-main-home .home-about",
            ".site-main-home .help-section",
            ".site-main-home .offer-section",
            ".site-main-home .cooperation-section",
            ".site-main-home .newsletter-cta-section",
            ".site-main-home .testimonials-section",
        ):
            self.assertIn(selector, continuity_styles)

        self.assertIn("padding-top: 0;", continuity_styles)
        self.assertIn("padding-bottom: 0;", continuity_styles)

    def test_home_section_surfaces_are_full_width_without_outer_rounding(self):
        continuity_styles = self.styles.split(
            "/* Strona glowna: sekcje lacza sie bez bialych szczelin", 1
        )[1]

        self.assertIn(".site-main-home > section > .site-container", continuity_styles)
        self.assertIn("width: 100%;", continuity_styles)
        self.assertIn("border-width: 0;", continuity_styles)
        self.assertIn("border-radius: 0;", continuity_styles)
        self.assertIn(".site-main-home + .site-footer", continuity_styles)
