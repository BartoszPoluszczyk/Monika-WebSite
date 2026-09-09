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
        self.assertIn("data-specializations-marquee", html)
        self.assertIn('class="specializations-marquee-track"', html)
        self.assertEqual(html.count('class="help-process-row"'), 3)
        self.assertEqual(html.count('class="specialization-band"'), 1)

    def test_cooperation_step_allows_an_editorial_photo(self):
        field = CooperationStep._meta.get_field("image")

        self.assertEqual(field.upload_to, "help_steps/")
        self.assertTrue(field.blank)
