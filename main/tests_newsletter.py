from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import NEWSLETTER_CONSENT_TEXT, HomePage, NewsletterSubscriber


class NewsletterHomeSectionTests(TestCase):
    def test_newsletter_section_is_rendered_before_testimonials(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()

        self.assertContains(response, "Zapisz się na newsletter")
        self.assertLess(
            content.index('id="newsletter"'),
            content.index('id="opinie"'),
        )

    def test_home_uses_newsletter_copy_from_admin_model(self):
        HomePage.objects.create(
            newsletter_title="Wiedza testowa",
            newsletter_description="Opis testowy newslettera",
            newsletter_button_label="Dołącz teraz",
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Wiedza testowa")
        self.assertContains(response, "Opis testowy newslettera")
        self.assertContains(response, "Dołącz teraz")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BOOKING_SITE_URL="https://example.com",
)
class NewsletterSignupTests(TestCase):
    def test_get_renders_signup_form(self):
        response = self.client.get(reverse("newsletter_signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Podaj swoje imię")
        self.assertContains(response, "Podaj swój adres e-mail")
        self.assertContains(response, "polityce prywatności")

    def test_valid_post_saves_subscriber_and_consent_snapshot(self):
        response = self.client.post(
            reverse("newsletter_signup"),
            data={
                "name": "  Anna   Kowalska ",
                "email": "ANNA@example.com",
                "consent": "on",
                "website": "",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('newsletter_signup')}?potwierdzenie=wyslane",
        )
        subscriber = NewsletterSubscriber.objects.get()
        self.assertEqual(subscriber.name, "Anna Kowalska")
        self.assertEqual(subscriber.email, "anna@example.com")
        self.assertTrue(subscriber.consent_confirmed)
        self.assertEqual(subscriber.consent_text, NEWSLETTER_CONSENT_TEXT)
        self.assertIsNotNone(subscriber.consented_at)
        self.assertFalse(subscriber.is_active)
        self.assertIsNone(subscriber.confirmed_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Potwierdź zapis", mail.outbox[0].subject)

    def test_consent_is_required(self):
        response = self.client.post(
            reverse("newsletter_signup"),
            data={
                "name": "Anna",
                "email": "anna@example.com",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zaznacz zgodę")
        self.assertFalse(NewsletterSubscriber.objects.exists())

    def test_active_email_cannot_be_added_twice_case_insensitively(self):
        NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            is_active=True,
        )

        response = self.client.post(
            reverse("newsletter_signup"),
            data={
                "name": "Anna ponownie",
                "email": "ANNA@example.com",
                "consent": "on",
                "website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "jest już zapisany")
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_inactive_email_can_subscribe_again(self):
        old = NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text="Stara treść zgody",
            is_active=False,
        )

        self.client.post(
            reverse("newsletter_signup"),
            data={
                "name": "Anna Nowa",
                "email": "ANNA@example.com",
                "consent": "on",
                "website": "",
            },
        )

        old.refresh_from_db()
        self.assertEqual(old.name, "Anna Nowa")
        self.assertEqual(old.email, "anna@example.com")
        self.assertFalse(old.is_active)
        self.assertIsNone(old.confirmed_at)
        self.assertEqual(old.consent_text, NEWSLETTER_CONSENT_TEXT)
        self.assertIsNone(old.unsubscribed_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_honeypot_blocks_bot_submission(self):
        response = self.client.post(
            reverse("newsletter_signup"),
            data={
                "name": "Robot",
                "email": "robot@example.com",
                "consent": "on",
                "website": "spam",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(NewsletterSubscriber.objects.exists())

    def test_success_message_is_shown_after_redirect(self):
        response = self.client.get(
            f"{reverse('newsletter_signup')}?potwierdzenie=wyslane"
        )

        self.assertContains(response, "Sprawdź swoją skrzynkę")


class PrivacyPolicyTests(TestCase):
    def test_privacy_policy_is_available(self):
        response = self.client.get(reverse("privacy_policy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administratorem danych")
