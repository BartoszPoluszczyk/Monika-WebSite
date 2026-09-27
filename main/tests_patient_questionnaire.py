from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from .models import PatientQuestionnaireDocument


class PatientQuestionnaireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = get_user_model().objects.create_user(
            username="ankieta-admin",
            password="test-password",
            is_staff=True,
        )

    def setUp(self):
        self.questionnaire = PatientQuestionnaireDocument(
            title="Ankieta testowa",
            is_active=True,
        )
        self.questionnaire.file.save(
            "ankieta-testowa.pdf",
            ContentFile(b"%PDF-1.4\n%%EOF"),
            save=True,
        )

    def tearDown(self):
        if self.questionnaire.file:
            self.questionnaire.file.delete(save=False)

    def test_home_links_to_questionnaire_after_testimonials(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()

        self.assertContains(response, "Testowa ankieta przed wizytą")
        self.assertContains(response, reverse("patient_questionnaire"))
        self.assertLess(content.index('id="opinie"'), content.index('id="ankieta-pacjenta"'))

    def test_questionnaire_preview_page_is_available(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("patient_questionnaire"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "personalna pacjenta")
        self.assertContains(response, reverse("patient_questionnaire_pdf"))

    def test_questionnaire_requires_staff_login(self):
        response = self.client.get(reverse("patient_questionnaire"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_questionnaire_pdf_is_served_privately(self):
        document_url = reverse("patient_questionnaire_pdf")

        anonymous_response = self.client.get(document_url)
        self.assertEqual(anonymous_response.status_code, 302)

        self.client.force_login(self.staff_user)
        response = self.client.get(document_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_only_latest_active_questionnaire_remains_active(self):
        replacement = PatientQuestionnaireDocument(
            title="Nowa ankieta",
            is_active=True,
        )
        replacement.file.save(
            "nowa-ankieta.pdf",
            ContentFile(b"%PDF-1.4\n%%EOF"),
            save=True,
        )
        self.addCleanup(replacement.file.delete, save=False)

        self.questionnaire.refresh_from_db()
        self.assertFalse(self.questionnaire.is_active)
        self.assertTrue(replacement.is_active)
