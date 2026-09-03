from decimal import Decimal
from functools import partial

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Appointment
from .emails import send_confirmation_notifications


PAYMENT_METHOD_TYPES = ["card", "blik", "p24"]


def payments_configured():
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)


def _configure_stripe():
    if not settings.STRIPE_SECRET_KEY:
        raise ImproperlyConfigured("Brakuje zmiennej STRIPE_SECRET_KEY.")
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _to_minor_units(amount):
    return int(Decimal(amount) * 100)


def create_checkout_session(appointment, request):
    _configure_stripe()
    if not appointment.payment_amount or not appointment.payment_expires_at:
        raise ValidationError("Rezerwacja nie ma poprawnie przygotowanej płatności.")

    metadata = {
        "appointment_public_id": str(appointment.public_id),
        "appointment_id": str(appointment.pk),
    }
    success_url = request.build_absolute_uri(
        reverse("booking:confirmation", args=[appointment.public_id])
    )
    success_url += "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(
        reverse("booking:payment_cancelled", args=[appointment.public_id])
    )

    session = stripe.checkout.Session.create(
        mode="payment",
        locale="pl",
        payment_method_types=PAYMENT_METHOD_TYPES,
        customer_email=appointment.email,
        client_reference_id=str(appointment.public_id),
        metadata=metadata,
        payment_intent_data={"metadata": metadata},
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": appointment.payment_currency.lower(),
                    "unit_amount": _to_minor_units(appointment.payment_amount),
                    "product_data": {
                        "name": appointment.service.name,
                        "description": (
                            f"Konsultacja {appointment.start_at:%d.%m.%Y o %H:%M}"
                        ),
                    },
                },
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        expires_at=int(appointment.payment_expires_at.timestamp()),
    )

    appointment.stripe_checkout_session_id = session.id
    appointment.save(update_fields=["stripe_checkout_session_id", "updated_at"])
    return session


def _session_value(session, key, default=None):
    if isinstance(session, dict):
        return session.get(key, default)
    return getattr(session, key, default)


def _session_metadata(session):
    metadata = _session_value(session, "metadata", {}) or {}
    return dict(metadata)


def mark_checkout_paid(session):
    metadata = _session_metadata(session)
    public_id = metadata.get("appointment_public_id")
    if not public_id:
        return False

    with transaction.atomic():
        appointment = Appointment.objects.select_for_update().filter(
            public_id=public_id
        ).first()
        if not appointment:
            return False

        session_id = _session_value(session, "id")
        if (
            appointment.stripe_checkout_session_id
            and appointment.stripe_checkout_session_id != session_id
        ):
            return False

        expected_amount = _to_minor_units(appointment.payment_amount or 0)
        amount_total = _session_value(session, "amount_total")
        currency = (_session_value(session, "currency", "") or "").upper()
        payment_status = _session_value(session, "payment_status")
        if (
            payment_status != "paid"
            or amount_total != expected_amount
            or currency != appointment.payment_currency.upper()
        ):
            return False

        should_notify = appointment.confirmation_email_sent_at is None
        appointment.status = Appointment.Status.CONFIRMED
        appointment.payment_status = Appointment.PaymentStatus.PAID
        appointment.paid_at = appointment.paid_at or timezone.now()
        appointment.payment_expires_at = None
        appointment.stripe_checkout_session_id = session_id
        appointment.stripe_payment_intent_id = (
            _session_value(session, "payment_intent") or ""
        )
        appointment.save(
            update_fields=[
                "status",
                "payment_status",
                "paid_at",
                "payment_expires_at",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "updated_at",
            ]
        )
        if should_notify:
            transaction.on_commit(
                partial(send_confirmation_notifications, appointment.pk),
                robust=True,
            )
        return True


def mark_checkout_failed(session):
    metadata = _session_metadata(session)
    public_id = metadata.get("appointment_public_id")
    if not public_id:
        return False

    return bool(
        Appointment.objects.filter(
            public_id=public_id,
            status=Appointment.Status.PENDING_PAYMENT,
            payment_status=Appointment.PaymentStatus.PENDING,
        ).update(
            status=Appointment.Status.CANCELLED,
            payment_status=Appointment.PaymentStatus.FAILED,
        )
    )


def retrieve_and_sync_checkout(session_id):
    _configure_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    mark_checkout_paid(session)
    return session


def expire_checkout_for_appointment(appointment):
    if not appointment.stripe_checkout_session_id or not settings.STRIPE_SECRET_KEY:
        return
    _configure_stripe()
    try:
        stripe.checkout.Session.expire(appointment.stripe_checkout_session_id)
    except stripe.StripeError:
        pass


def construct_webhook_event(payload, signature):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ImproperlyConfigured("Brakuje zmiennej STRIPE_WEBHOOK_SECRET.")
    return stripe.Webhook.construct_event(
        payload,
        signature,
        settings.STRIPE_WEBHOOK_SECRET,
    )
