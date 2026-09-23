from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import LegalDocument, SiteSettings


class LegalDocumentTests(TestCase):
    def test_initial_documents_are_published(self):
        for kind in (
            LegalDocument.DocumentType.TERMS,
            LegalDocument.DocumentType.PRIVACY,
            LegalDocument.DocumentType.COOKIES,
        ):
            with self.subTest(kind=kind):
                self.assertIsNotNone(LegalDocument.current(kind))

    def test_future_version_does_not_replace_current(self):
        current = LegalDocument.current(LegalDocument.DocumentType.TERMS)
        LegalDocument.objects.create(
            document_type=LegalDocument.DocumentType.TERMS,
            title="Nowy regulamin",
            version="2.0",
            effective_from=timezone.localdate() + timedelta(days=1),
            content="Przyszła treść",
            is_published=True,
        )
        self.assertEqual(LegalDocument.current(LegalDocument.DocumentType.TERMS), current)

    def test_markers_use_site_settings(self):
        settings = SiteSettings.objects.create(
            owner_name="Monika Kulik",
            business_name="Testowa działalność",
            business_address="ul. Testowa 1",
            tax_id="1234567890",
            contact_email="kontakt@example.com",
            contact_phone="500600700",
        )
        rendered = LegalDocument.current(
            LegalDocument.DocumentType.PRIVACY
        ).rendered_content(settings)
        self.assertIn("Testowa działalność", rendered)
        self.assertIn("kontakt@example.com", rendered)
        self.assertNotIn("{{EMAIL}}", rendered)


class LegalPagesTests(TestCase):
    def test_all_legal_pages_are_available(self):
        for route_name in ("terms_of_service", "privacy_policy", "cookie_policy"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Wersja 1.0")

    def test_footer_links_to_documents(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("terms_of_service"))
        self.assertContains(response, reverse("privacy_policy"))
        self.assertContains(response, reverse("cookie_policy"))

    def test_notice_only_mentions_technical_cookies(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "wyłącznie techniczne pliki cookies")
        self.assertNotContains(response, "Akceptuj wszystkie")
