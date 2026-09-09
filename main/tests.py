import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image
from fontTools.ttLib import TTFont

from django.contrib.staticfiles import finders
from django.db import connection
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import AboutPage, HomePage, SiteSettings


class WebsitePaletteTests(SimpleTestCase):
    def test_website_uses_monikas_current_brand_palette(self):
        css = Path(finders.find("css/style.css")).read_text(encoding="utf-8")
        for declaration in (
            "--palette-green-accent: #6F8F74;",
            "--palette-green-pastel: #E4ECE7;",
            "--palette-green-pastel-strong: #BDD0C0;",
            "--palette-navy: #102F3A;",
            "--palette-orange: #D98262;",
            "--palette-white: #FFFFFF;",
            "--color-surface-page: var(--palette-white);",
            "--color-text-primary: var(--palette-navy);",
            "--color-accent: var(--palette-green-accent);",
            "--color-cta-background: var(--palette-orange);",
            "--color-secondary-button-background: var(--palette-navy);",
            "--color-feedback-border: var(--palette-orange);",
        ):
            with self.subTest(declaration=declaration):
                self.assertIn(declaration, css)

    def test_yellow_and_legacy_olive_palette_are_not_used_in_public_styles(self):
        for asset in ("css/style.css", "css/calorie-calculator.css"):
            css = Path(finders.find(asset)).read_text(encoding="utf-8").lower()
            for obsolete in ("#f0cf60", "#a9c3a2", "#f7f1ec", "#301280", "#c51818", "#738356", "#59683f", "#9aa681", "#f4e6eb", "#faf5e8", "#faf4e8"):
                with self.subTest(asset=asset, color=obsolete):
                    self.assertNotIn(obsolete, css)

    def test_about_page_uses_shared_brand_button_without_bootstrap_warning_colors(self):
        html = render_to_string("main/about.html")
        self.assertIn('class="button-primary mt-2"', html)
        self.assertIn('class="about-empty-message"', html)
        self.assertNotIn("btn-primary", html)
        self.assertNotIn("alert-warning", html)

    def test_booking_emails_use_the_current_brand_palette(self):
        templates = Path(__file__).resolve().parent.parent / "booking" / "templates" / "booking" / "emails"
        appointment_email = (templates / "appointment.html").read_text(encoding="utf-8")
        manager_email = (templates / "manager.html").read_text(encoding="utf-8")
        for color in ("#E4ECE7", "#BDD0C0", "#6F8F74", "#102F3A"):
            with self.subTest(color=color):
                self.assertIn(color, appointment_email)
                self.assertIn(color, manager_email)
        self.assertIn("#D98262", appointment_email)


class NavbarBrandingTests(SimpleTestCase):
    logo_path = "images/branding/monika-kulik-logo-pionowe.svg"

    def test_calculator_link_is_available_in_shared_navigation(self):
        html = render_to_string("main/partials/navbar.html")
        self.assertIn(f'href="{reverse("calorie_calculator")}"', html)
        self.assertIn("Kalkulator kalorii", html)
        self.assertIn('class="navigation-icon"', html)
        self.assertIn('class="navbar-signature"', html)

    def test_sidebar_signature_has_four_lines_and_one_continuous_footer(self):
        html = render_to_string("main/partials/navbar.html")
        for line in ("Zdrowie", "zaczyna się", "od dobrych", "wyborów"):
            self.assertIn(f"<span>{line}</span>", html)
        footer = html.split('<div class="navbar-footer">', 1)[1].split("</div>", 1)[0]
        self.assertIn("navbar-bottom-decoration.svg", footer)
        self.assertIn('class="navbar-cta"', footer)
        self.assertIn('href="' + reverse("booking:book") + '"', footer)

    def test_navbar_has_no_top_wave_but_keeps_the_bottom_wave(self):
        html = render_to_string("main/partials/navbar.html")
        self.assertNotIn("navbar-top-decoration.svg", html)
        self.assertNotIn('class="navbar-corner"', html)
        self.assertIn("navbar-bottom-decoration.svg", html)

    def test_navigation_assets_are_local_and_loaded_by_the_shared_base(self):
        html = render_to_string("main/base.html")
        for asset in (
            "css/navigation.css",
            "js/navigation.js",
            "fonts/caveat-latin.woff2",
            "fonts/amsterdam-one.ttf",
        ):
            self.assertIsNotNone(finders.find(asset))
            self.assertIn(asset, html)
        css = Path(finders.find("css/navigation.css")).read_text(encoding="utf-8")
        self.assertIn('font-family: "Amsterdam One", "Caveat", cursive;', css)
        self.assertIn('src: url("../fonts/amsterdam-one.ttf") format("truetype");', css)
        self.assertIn("padding-left: var(--navbar-width)", css)
        self.assertNotIn("radial-gradient", css)

    def test_amsterdam_one_signature_font_is_embedded_with_polish_fallback(self):
        font = TTFont(finders.find("fonts/amsterdam-one.ttf"))
        family_names = {
            record.toUnicode()
            for record in font["name"].names
            if record.nameID in (1, 4)
        }
        self.assertIn("Amsterdam One", family_names)
        # The supplied regular face lacks e-ogonek. Keep the text correct and
        # let the explicit Caveat fallback draw only that character.
        self.assertNotIn(ord("ę"), font.getBestCmap())

    def test_decorations_are_filled_paths_not_disconnected_rings(self):
        for filename, viewbox in (
            ("navbar-top-decoration.svg", "0 0 180 120"),
            ("navbar-bottom-decoration.svg", "0 0 180 330"),
        ):
            root = ET.parse(finders.find("images/branding/" + filename)).getroot()
            self.assertEqual(root.get("viewBox"), viewbox)
            self.assertEqual(root.get("preserveAspectRatio"), "none")
            for element in root:
                self.assertEqual(element.tag.rsplit("}", 1)[-1], "path")
                self.assertTrue(element.get("d").endswith("Z"))

    def test_mobile_menu_has_a_single_toggle_controller(self):
        html = render_to_string("main/partials/navbar.html")
        self.assertIn('aria-controls="mainNavigation"', html)
        self.assertIn('aria-expanded="false"', html)
        self.assertNotIn("data-bs-toggle", html)

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
        self.assertEqual(root.get("viewBox"), "300 407.5 529 650.5")
        tags = {element.tag.rsplit("}", 1)[-1] for element in root.iter()}
        self.assertLessEqual(tags, {"svg", "title", "desc", "path"})
        self.assertIn("path", tags)
        self.assertIn('fill="#6F8F74"', Path(logo).read_text(encoding="utf-8"))
        for element in root.iter():
            for name in element.attrib:
                attribute = name.rsplit("}", 1)[-1].lower()
                self.assertNotEqual(attribute, "href")
                self.assertFalse(attribute.startswith("on"))


class WebsitePortraitTests(SimpleTestCase):
    hero_asset = "images/portraits/monika-kulik-hero-20260903.webp"
    about_asset = "images/portraits/monika-kulik-about-20260903.webp"

    def test_home_hero_has_optimized_default_and_eager_loading(self):
        html = render_to_string("main/partials/hero.html")
        self.assertIn(self.hero_asset, html)
        self.assertIn('fetchpriority="high"', html)
        self.assertNotIn('loading="lazy"', html)
        self.assertIn('width="1073"', html)
        self.assertIn('height="1466"', html)
        self.assertNotIn("images/monika.png", html)

    def test_about_preview_uses_portrait_and_loads_lazily(self):
        html = render_to_string("main/partials/about_preview.html")
        self.assertIn(self.about_asset, html)
        self.assertIn('loading="lazy"', html)
        self.assertNotIn(self.hero_asset, html)

    def test_dedicated_about_page_uses_same_default_portrait(self):
        html = render_to_string("main/about.html", {"about_page": AboutPage(title="O mnie", description="Opis bez zmian")})
        self.assertIn(self.about_asset, html)
        self.assertIn("Opis bez zmian", html)

    def test_admin_hero_photo_and_text_still_take_precedence(self):
        page = HomePage(hero_photo="home/hero/custom.png", hero_title="Własny tytuł")
        page.hero_photo._dimensions_cache = (900, 1200)
        html = render_to_string("main/partials/hero.html", {"home_page": page})
        self.assertIn(page.hero_photo.url, html)
        self.assertIn('width="900"', html)
        self.assertIn('height="1200"', html)
        self.assertIn("Własny tytuł", html)
        self.assertNotIn(self.hero_asset, html)

    def test_admin_about_photo_takes_precedence_on_both_pages(self):
        page = AboutPage(photo="about/custom.png", title="O mnie", description="Mój opis")
        page.photo._dimensions_cache = (800, 1000)
        for template in ("main/partials/about_preview.html", "main/about.html"):
            with self.subTest(template=template):
                html = render_to_string(template, {"about_page": page})
                self.assertIn(page.photo.url, html)
                self.assertIn('width="800"', html)
                self.assertIn("Mój opis", html)
                self.assertNotIn(self.about_asset, html)

    def test_web_images_keep_dimensions_and_hero_transparency(self):
        for asset, has_alpha in ((self.hero_asset, True), (self.about_asset, False)):
            with self.subTest(asset=asset):
                path = finders.find(asset)
                self.assertIsNotNone(path)
                with Image.open(path) as portrait:
                    self.assertEqual(portrait.size, (1073, 1466))
                    self.assertEqual(portrait.format, "WEBP")
                    self.assertEqual("A" in portrait.getbands(), has_alpha)
                    if has_alpha:
                        self.assertEqual(portrait.getpixel((0, 0))[3], 0)
                        self.assertEqual(portrait.getpixel((550, 300))[3], 255)


class HomeHeroPhotoTests(TestCase):
    photo_asset = "images/backgrounds/monika-kitchen-20260909.webp"

    def test_background_wraps_only_hero_and_about_keeps_its_own_portrait(self):
        class IntroParser(HTMLParser):
            depth = 0
            sections = None
            photos = 0

            def __init__(self):
                super().__init__()
                self.sections = []

            def handle_starttag(self, tag, attributes):
                attrs = dict(attributes)
                if tag == "div":
                    if self.depth or attrs.get("class") == "home-photo-intro":
                        self.depth += 1
                if self.depth and tag == "section":
                    self.sections.append(attrs.get("class"))
                if self.depth and tag == "img":
                    if attrs.get("class") == "home-photo-background":
                        self.photos += 1

            def handle_endtag(self, tag):
                if tag == "div" and self.depth:
                    self.depth -= 1

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        parser = IntroParser()
        parser.feed(response.content.decode())
        self.assertEqual(parser.sections, ["hero"])
        self.assertEqual(parser.photos, 1)
        self.assertContains(response, self.photo_asset, count=1)
        self.assertNotContains(response, 'class="hero-person"')
        self.assertContains(response, 'class="home-about-image"', count=1)
        for anchor in ('id="o-mnie"', 'id="pomoc"', 'id="oferta"', 'id="wspolpraca"'):
            self.assertContains(response, anchor)

    def test_other_pages_do_not_load_the_home_photo_or_its_styles(self):
        for name in ("about", "calorie_calculator", "booking:book"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, self.photo_asset)
                self.assertNotContains(response, "css/home-photo.css")

    def test_hero_background_preserves_admin_text_and_independent_about_portrait(self):
        home = HomePage(
            hero_title="Indywidualny tytuł",
            hero_description="Indywidualny opis strony",
            hero_photo="home/hero/custom.png",
        )
        about = AboutPage(
            title="O mnie", subtitle="Indywidualny podtytuł",
            description="Opis Moniki z panelu administratora.", photo="about/custom.png",
        )
        about.photo._dimensions_cache = (800, 1000)
        html = render_to_string("main/home.html", {"home_page": home, "about_page": about})
        for content in (home.hero_title, home.hero_description, about.subtitle, about.description):
            self.assertIn(content, html)
        self.assertNotIn(home.hero_photo.url, html)
        self.assertIn(about.photo.url, html)

    def test_background_keeps_the_full_source_frame_in_a_small_web_asset(self):
        path = Path(finders.find(self.photo_asset))
        self.assertLess(path.stat().st_size, 300_000)
        with Image.open(path) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (1821, 864))
            image.verify()


class CalorieCalculatorPageTests(TestCase):
    def test_page_renders_with_active_navigation_and_no_database_writes(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("calorie_calculator"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/calorie_calculator.html")
        self.assertContains(response, "Ile energii")
        self.assertContains(response, "Oblicz zapotrzebowanie")
        self.assertContains(response, 'class="navigation-link is-active"')
        self.assertContains(response, 'aria-current="page"', count=1)
        for query in queries:
            self.assertTrue(query["sql"].lstrip().upper().startswith("SELECT"), query["sql"])

    def test_calculation_is_local_and_sources_and_limitations_are_visible(self):
        response = self.client.get(reverse("calorie_calculator"))
        self.assertContains(response, 'type="module"')
        self.assertContains(response, "js/calorie-calculator.mjs")
        self.assertContains(response, "Nie wysyłamy ich na serwer")
        self.assertContains(response, "Dla osób pełnoletnich")
        self.assertContains(response, "W ciąży nie wyznaczamy celu redukcji")
        self.assertContains(response, "uproszczony wzór Harrisa–Benedicta")
        self.assertContains(response, "https://dietoterapia-lenartowicz.pl/kalkulator-zapotrzebowania-kalorycznego")
        self.assertContains(response, 'id="calculate-button" type="submit" disabled')
        self.assertContains(response, "<noscript>")
        for field in ("age", "height", "weight", "condition", "trimester", "steps", "trainingType", "frequency"):
            self.assertNotContains(response, f'name="{field}"')

    def test_four_steps_and_all_reference_variables_are_present(self):
        response = self.client.get(reverse("calorie_calculator"))
        self.assertContains(response, 'data-calorie-step=', count=4)
        self.assertContains(response, 'data-step-link=', count=4)
        for field in ("sex", "age", "height", "weight", "condition", "trimester", "work", "steps", "training", "trainingType", "frequency", "goal"):
            self.assertContains(response, f'data-field="{field}"')
        for result in ("target", "resting", "maintenance", "activity", "condition", "goal"):
            self.assertContains(response, f'id="{result}-value"')

    def test_calculator_does_not_accept_patient_data_posts(self):
        response = self.client.post(reverse("calorie_calculator"), {"weight": "70"})
        self.assertEqual(response.status_code, 405)

    def test_calculator_assets_are_discoverable(self):
        for asset in ("css/calorie-calculator.css", "js/calorie-calculator.mjs", "js/calorie-calculator-core.mjs"):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
