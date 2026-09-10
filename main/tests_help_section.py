from django.template.loader import render_to_string
from django.test import SimpleTestCase

from main.models import CooperationStep, HomePage, Specialization


class HelpSectionTests(SimpleTestCase):
    def test_help_section_renders_editorial_process_and_dynamic_bands(self):
        home_page = HomePage(
            help_eyebrow="Indywidualne podejście",
            help_title="Jak pomagam?",
            help_lead="Od poznania historii do planu, który działa.",
            help_description="Wspieram przez **odŻYWIENIE**.",
            help_specializations_title="Moje specjalności",
        )
        steps = [
            CooperationStep(title="Poznaję punkt wyjścia", description="Opis pierwszego etapu", order=1),
            CooperationStep(title="Tworzę plan", description="Opis drugiego etapu", order=2),
            CooperationStep(title="Towarzyszę w zmianie", description="Opis trzeciego etapu", order=3),
        ]
        specializations = [Specialization(name="Dieta kliniczna", description="Opis", order=1)]

        html = render_to_string(
            "main/partials/help.html",
            {
                "home_page": home_page,
                "cooperation_steps": steps,
                "specializations": specializations,
            },
        )

        self.assertIn("Jak pomagam?", html)
        self.assertIn("Od poznania historii do planu, który działa.", html)
        self.assertIn('<span class="content-accent">odŻYWIENIE</span>', html)
        self.assertIn("data-specializations-reveal", html)
        self.assertIn('class="specializations-list"', html)
        self.assertEqual(html.count('class="help-process-row"'), 3)
        self.assertEqual(html.count('class="specialization-band"'), 1)

    def render_specializations(self, specializations):
        return render_to_string(
            "main/partials/help.html",
            {"home_page": HomePage(), "cooperation_steps": [], "specializations": specializations},
        )

    def test_specializations_are_single_list_items_in_admin_order(self):
        specializations = [
            Specialization(name=f"Specjalność {index}", description=f"Opis {index}")
            for index in range(9)
        ]

        html = self.render_specializations(specializations)

        self.assertEqual(html.count('<li class="specialization-band">'), 9)
        for index in range(9):
            self.assertEqual(html.count(f"Specjalność {index}"), 1)
            self.assertEqual(html.count(f"Opis {index}"), 1)
        self.assertLess(html.index("Specjalność 0"), html.index("Specjalność 8"))
        self.assertIn('aria-labelledby="specializations-title"', html)
        self.assertNotIn("marquee", html)
        self.assertNotIn("specialization-band-number", html)
        self.assertNotIn("specialization-band-arrow", html)
        self.assertNotIn("is-reveal-pending", html)  # Visible before JS / without JS.

    def test_specialization_without_description_does_not_get_placeholder_copy(self):
        html = self.render_specializations([Specialization(name="Moja specjalność")])
        band = html.split('<li class="specialization-band">')[1].split("</li>")[0]

        self.assertIn("Moja specjalność", band)
        self.assertNotIn("<p>", band)

    def test_specialization_content_stays_escaped(self):
        html = self.render_specializations([
            Specialization(name='<script>alert("name")</script>', description='<img src=x onerror="alert(1)">'),
        ])

        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;img", html)

    def test_empty_specializations_render_message_without_empty_animation(self):
        html = self.render_specializations([])

        self.assertIn("Specjalności pojawią się tutaj wkrótce.", html)
        self.assertNotIn("data-specializations-reveal", html)

    def test_cooperation_step_allows_an_editorial_photo(self):
        field = CooperationStep._meta.get_field("image")

        self.assertEqual(field.upload_to, "help_steps/")
        self.assertTrue(field.blank)
