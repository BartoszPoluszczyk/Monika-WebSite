from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    NEWSLETTER_CONSENT_TEXT,
    NewsletterCampaign,
    NewsletterDelivery,
    NewsletterSubscriber,
)
from .newsletter import send_campaign, send_test_campaign


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BOOKING_SITE_URL="https://example.com",
)
class NewsletterConfirmationTests(TestCase):
    def test_confirmation_activates_subscriber(self):
        subscriber = NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            is_active=False,
        )

        response = self.client.get(
            reverse(
                "newsletter_confirm",
                args=[subscriber.confirmation_token],
            )
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)
        self.assertIsNotNone(subscriber.confirmed_at)

    def test_old_confirmation_link_does_not_reactivate_unsubscribed_address(self):
        subscriber = NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            confirmed_at=timezone.now(),
            is_active=False,
            unsubscribed_at=timezone.now(),
        )

        response = self.client.get(
            reverse(
                "newsletter_confirm",
                args=[subscriber.confirmation_token],
            )
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        self.assertContains(response, "Zapis pozostaje")

    def test_unsubscribe_requires_post_and_deactivates_subscription(self):
        subscriber = NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            confirmed_at=timezone.now(),
            is_active=True,
        )
        url = reverse(
            "newsletter_unsubscribe",
            args=[subscriber.unsubscribe_token],
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        self.assertIsNotNone(subscriber.unsubscribed_at)
        self.assertContains(response, "Adres został")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BOOKING_SITE_URL="https://example.com",
)
class NewsletterCampaignTests(TestCase):
    def setUp(self):
        self.active_subscriber = NewsletterSubscriber.objects.create(
            name="Anna",
            email="anna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            confirmed_at=timezone.now(),
            is_active=True,
        )
        self.inactive_subscriber = NewsletterSubscriber.objects.create(
            name="Nieaktywna",
            email="nieaktywna@example.com",
            consent_confirmed=True,
            consent_text=NEWSLETTER_CONSENT_TEXT,
            confirmed_at=timezone.now(),
            is_active=False,
        )
        self.campaign = NewsletterCampaign.objects.create(
            title="Jesienne wskazówki",
            subject="Jak zadbać o odporność?",
            preheader="Trzy praktyczne wskazówki.",
            heading="Zdrowa jesień",
            content="Pierwszy akapit.\n\nDrugi akapit.",
            button_label="Przeczytaj więcej",
            button_url="https://example.com/artykul/",
            status=NewsletterCampaign.Status.READY,
        )

    def test_campaign_is_sent_only_to_confirmed_active_subscribers(self):
        sent_count, failed_count = send_campaign(self.campaign.pk)

        self.assertEqual((sent_count, failed_count), (1, 0))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["anna@example.com"])
        self.assertIn("Jak zadbać", mail.outbox[0].subject)
        self.assertIn(
            str(self.active_subscriber.unsubscribe_token),
            mail.outbox[0].body,
        )
        self.assertEqual(NewsletterDelivery.objects.count(), 1)
        delivery = NewsletterDelivery.objects.get()
        self.assertEqual(delivery.status, NewsletterDelivery.Status.SENT)

        self.campaign.refresh_from_db()
        self.assertEqual(
            self.campaign.status,
            NewsletterCampaign.Status.SENT,
        )
        self.assertEqual(self.campaign.recipient_count, 1)
        self.assertEqual(self.campaign.failed_count, 0)

    def test_sent_campaign_cannot_be_sent_again(self):
        send_campaign(self.campaign.pk)

        with self.assertRaisesMessage(
            ValueError,
            "została już wysłana",
        ):
            send_campaign(self.campaign.pk)

        self.assertEqual(len(mail.outbox), 1)

    def test_draft_can_be_sent_as_test_without_changing_status(self):
        self.campaign.status = NewsletterCampaign.Status.DRAFT
        self.campaign.save(update_fields=["status"])

        sent = send_test_campaign(
            self.campaign,
            "monika@example.com",
        )

        self.assertEqual(sent, 1)
        self.assertEqual(mail.outbox[0].to, ["monika@example.com"])
        self.assertTrue(mail.outbox[0].subject.startswith("[TEST]"))
        self.campaign.refresh_from_db()
        self.assertEqual(
            self.campaign.status,
            NewsletterCampaign.Status.DRAFT,
        )

    def test_due_campaign_is_sent_by_management_command(self):
        self.campaign.scheduled_at = timezone.now() - timedelta(minutes=1)
        self.campaign.save(update_fields=["scheduled_at"])

        call_command("send_scheduled_newsletters")

        self.campaign.refresh_from_db()
        self.assertEqual(
            self.campaign.status,
            NewsletterCampaign.Status.SENT,
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_future_campaign_is_not_sent_by_management_command(self):
        self.campaign.scheduled_at = timezone.now() + timedelta(days=1)
        self.campaign.save(update_fields=["scheduled_at"])

        call_command("send_scheduled_newsletters")

        self.campaign.refresh_from_db()
        self.assertEqual(
            self.campaign.status,
            NewsletterCampaign.Status.READY,
        )
        self.assertEqual(len(mail.outbox), 0)
