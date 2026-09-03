import xml.etree.ElementTree as ET

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import SimpleTestCase

from .models import SiteSettings


class NavbarBrandingTests(SimpleTestCase):
    logo_path = "images/branding/monika-kulik-logo-horizontal.svg"

    def test_final_logo_is_default_without_settings(self):
        html = render_to_string("main/partials/navbar.html")
        self.assertIn(self.logo_path, html)
        self.assertIn("Monika Kulik — dietetyk kliniczny, strona główna", html)
        self.assertNotIn("Monika Kowalska", html)

    def test_empty_admin_logo_uses_default_without_changing_site_name(self):
        settings = SiteSettings(site_name="Zdrowienie przez żywienie")
        html = render_to_string("main/partials/navbar.html", {"site_settings": settings})
        self.assertIn(self.logo_path, html)
        self.assertEqual(settings.site_name, "Zdrowienie przez żywienie")
        self.assertFalse(settings.logo)

    def test_admin_uploaded_logo_still_takes_precedence(self):
        settings = SiteSettings(site_name="Moja poradnia", logo="branding/custom.png")
        html = render_to_string("main/partials/navbar.html", {"site_settings": settings})
        self.assertIn(settings.logo.url, html)
        self.assertIn('alt="Moja poradnia"', html)
        self.assertNotIn(self.logo_path, html)

    def test_web_logo_is_self_contained_vector_without_background(self):
        logo = finders.find(self.logo_path)
        self.assertIsNotNone(logo)
        root = ET.parse(logo).getroot()
        self.assertEqual(root.get("viewBox"), "0 0 682 138")
        tags = {element.tag.rsplit("}", 1)[-1] for element in root.iter()}
        self.assertLessEqual(tags, {"svg", "title", "desc", "g", "path"})
        self.assertIn("path", tags)
        for element in root.iter():
            for name in element.attrib:
                attribute = name.rsplit("}", 1)[-1].lower()
                self.assertNotEqual(attribute, "href")
                self.assertFalse(attribute.startswith("on"))
