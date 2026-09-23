from types import SimpleNamespace
import uuid

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from .models import (
    NewsletterCampaign,
    NewsletterDelivery,
    NewsletterSubscriber,
    SiteSettings,
)


def _site_settings():
    return SiteSettings.objects.first()


def _site_name():
    site_settings = _site_settings()
    return site_settings.site_name if site_settings else "Dietetyk Monika"


def _reply_to():
    site_settings = _site_settings()
    if site_settings and site_settings.contact_email:
        return [site_settings.contact_email]
    return []


def _absolute_url(path):
    if path.startswith(("http://", "https://")):
        return path
    base_url = settings.BOOKING_SITE_URL.rstrip("/")
    return f"{base_url}/{path.lstrip('/')}"


def build_campaign_context(campaign, subscriber=None):
    unsubscribe_url = "#"
    subscriber_name = "Moniko"
    if subscriber is not None:
        subscriber_name = subscriber.name
        unsubscribe_url = _absolute_url(
            reverse(
                "newsletter_unsubscribe",
                args=[subscriber.unsubscribe_token],
            )
        )

    image_url = ""
    if campaign.image:
        image_url = _absolute_url(campaign.image.url)

    return {
        "campaign": campaign,
        "subscriber_name": subscriber_name,
        "site_name": _site_name(),
        "image_url": image_url,
        "unsubscribe_url": unsubscribe_url,
    }


def _send_templated_email(*, subject, recipients, text_template, html_template, context):
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        reply_to=_reply_to(),
    )
    message.attach_alternative(html_body, "text/html")
    return message.send(fail_silently=False)


def send_confirmation_email(subscriber):
    confirmation_url = _absolute_url(
        reverse(
            "newsletter_confirm",
            args=[subscriber.confirmation_token],
        )
    )
    sent = _send_templated_email(
        subject=f"Potwierdź zapis do newslettera — {_site_name()}",
        recipients=[subscriber.email],
        text_template="main/emails/newsletter_confirmation.txt",
        html_template="main/emails/newsletter_confirmation.html",
        context={
            "subscriber": subscriber,
            "confirmation_url": confirmation_url,
            "site_name": _site_name(),
        },
    )
    if sent:
        NewsletterSubscriber.objects.filter(pk=subscriber.pk).update(
            confirmation_sent_at=timezone.now()
        )
    return sent


def send_test_campaign(campaign, recipient_email):
    preview_subscriber = SimpleNamespace(
        name="Monika",
        email=recipient_email,
        unsubscribe_token=uuid.uuid4(),
    )
    return _send_templated_email(
        subject=f"[TEST] {campaign.subject}",
        recipients=[recipient_email],
        text_template="main/emails/newsletter_campaign.txt",
        html_template="main/emails/newsletter_campaign.html",
        context=build_campaign_context(campaign, preview_subscriber),
    )


def send_campaign(campaign_id, *, force=False):
    with transaction.atomic():
        campaign = NewsletterCampaign.objects.select_for_update().get(
            pk=campaign_id
        )
        if campaign.status == NewsletterCampaign.Status.SENT:
            raise ValueError("Ta kampania została już wysłana.")
        if campaign.status == NewsletterCampaign.Status.SENDING:
            raise ValueError("Ta kampania jest już wysyłana.")
        if campaign.status != NewsletterCampaign.Status.READY:
            raise ValueError(
                "Przed wysyłką ustaw status kampanii na „Gotowa do wysyłki”."
            )
        if (
            campaign.scheduled_at
            and campaign.scheduled_at > timezone.now()
            and not force
        ):
            raise ValueError("Termin wysyłki tej kampanii jeszcze nie nadszedł.")

        campaign.status = NewsletterCampaign.Status.SENDING
        campaign.save(update_fields=["status", "updated_at"])

    subscribers = NewsletterSubscriber.objects.filter(
        consent_confirmed=True,
        is_active=True,
        confirmed_at__isnull=False,
        unsubscribed_at__isnull=True,
    ).order_by("pk")

    for subscriber in subscribers.iterator():
        delivery, _ = NewsletterDelivery.objects.get_or_create(
            campaign=campaign,
            subscriber=subscriber,
            defaults={"subscriber_email": subscriber.email},
        )
        if delivery.status == NewsletterDelivery.Status.SENT:
            continue

        delivery.subscriber_email = subscriber.email
        delivery.error_message = ""
        try:
            sent = _send_templated_email(
                subject=campaign.subject,
                recipients=[subscriber.email],
                text_template="main/emails/newsletter_campaign.txt",
                html_template="main/emails/newsletter_campaign.html",
                context=build_campaign_context(campaign, subscriber),
            )
            if not sent:
                raise RuntimeError("Backend pocztowy nie potwierdził wysłania.")
        except Exception as error:
            delivery.status = NewsletterDelivery.Status.FAILED
            delivery.error_message = str(error)[:2000]
            delivery.sent_at = None
        else:
            delivery.status = NewsletterDelivery.Status.SENT
            delivery.sent_at = timezone.now()
        delivery.save(
            update_fields=[
                "subscriber_email",
                "status",
                "sent_at",
                "error_message",
                "updated_at",
            ]
        )

    sent_count = campaign.deliveries.filter(
        status=NewsletterDelivery.Status.SENT
    ).count()
    failed_count = campaign.deliveries.filter(
        status=NewsletterDelivery.Status.FAILED
    ).count()
    NewsletterCampaign.objects.filter(pk=campaign.pk).update(
        status=NewsletterCampaign.Status.SENT,
        sent_at=timezone.now(),
        recipient_count=sent_count,
        failed_count=failed_count,
    )
    return sent_count, failed_count


def send_due_campaigns(now=None):
    now = now or timezone.now()
    campaign_ids = NewsletterCampaign.objects.filter(
        status=NewsletterCampaign.Status.READY,
        scheduled_at__isnull=False,
        scheduled_at__lte=now,
    ).values_list("pk", flat=True)

    results = []
    for campaign_id in campaign_ids.iterator():
        try:
            sent_count, failed_count = send_campaign(campaign_id)
        except ValueError:
            continue
        results.append((campaign_id, sent_count, failed_count))
    return results
