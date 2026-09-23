from django.test import TestCase
from django.urls import reverse

from .models import SiteSettings


class ContactPageTests(TestCase):
    def setUp(self):
        self.settings = SiteSettings.objects.create(
            contact_heading="Porozmawiajmy",
            contact_description="Opis kontaktu Moniki.",
            contact_email="kontakt@example.com",
            contact_phone="+48 500 600 700",
            contact_address="ul. Zdrowa 1\n90-001 Łódź",
            contact_hours="Poniedziałek–piątek, 9:00–17:00",
            google_maps_url="https://maps.google.com/?q=lodz",
            instagram_url="https://www.instagram.com/monika",
        )

    def test_contact_page_uses_admin_managed_details(self):
        response = self.client.get(reverse("contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Porozmawiajmy")
        self.assertContains(response, "kontakt@example.com")
        self.assertContains(response, "+48 500 600 700")
        self.assertContains(response, "ul. Zdrowa 1")
        self.assertContains(response, "Poniedziałek–piątek")
        self.assertContains(response, self.settings.instagram_url)
        self.assertContains(response, self.settings.google_maps_url)

    def test_contact_navigation_item_is_active(self):
        response = self.client.get(reverse("contact"))

        self.assertContains(response, 'href="/kontakt/"')
        self.assertContains(response, 'aria-current="page"')

    def test_contact_page_is_available_without_configured_settings(self):
        SiteSettings.objects.all().delete()

        response = self.client.get(reverse("contact"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dane kontaktowe pojawią się tutaj wkrótce.")
