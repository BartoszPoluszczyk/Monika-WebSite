from django.template.loader import render_to_string
from django.test import SimpleTestCase

from main.models import CooperationStep, HomePage, Specialization


class HelpSectionTests(SimpleTestCase):
    def test_help_section_renders_admin_content_process_and_slider(self):
        home_page = HomePage(
            help_eyebrow="Jak pomagam",
            help_title="Plan, który działa",
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

        self.assertIn("Plan, który działa", html)
        self.assertIn('<span class="content-accent">odŻYWIENIE</span>', html)
        self.assertIn('data-specializations-carousel', html)
        self.assertIn('class="specializations-track"', html)
        self.assertEqual(html.count('class="help-step"'), 3)
