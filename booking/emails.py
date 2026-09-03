from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from main.models import SiteSettings

from .models import Appointment
from .services import get_booking_settings


def _site_name():
    site_settings = SiteSettings.objects.first()
    return site_settings.site_name if site_settings else "Dietetyk Monika"


def _absolute_url(path):
    return f"{settings.BOOKING_SITE_URL}{path}"


def _appointment_context(appointment, **extra):
    booking_settings = get_booking_settings()
    context = {
        "appointment": appointment,
        "site_name": _site_name(),
        "start_local": timezone.localtime(appointment.start_at),
        "previous_start_local": (
            timezone.localtime(appointment.previous_start_at)
            if appointment.previous_start_at
            else None
        ),
        "manage_url": _absolute_url(
            reverse("booking:confirmation", args=[appointment.public_id])
        ),
        "cancel_url": _absolute_url(
            reverse("booking:cancel", args=[appointment.public_id])
        ),
        "reschedule_url": _absolute_url(
            reverse("booking:reschedule", args=[appointment.public_id])
        ),
        "calendar_url": _absolute_url(
            reverse("booking:calendar_file", args=[appointment.public_id])
        ),
        "new_booking_url": _absolute_url(
            f"{reverse('booking:book')}?service={appointment.service_id}"
        ),
        "cancellation_notice_hours": booking_settings.cancellation_notice_hours,
    }
    context.update(extra)
    return context


def _send_email(*, subject, recipients, template_name, context, reply_to=None):
    text_body = render_to_string(f"booking/emails/{template_name}.txt", context)
    html_body = render_to_string(f"booking/emails/{template_name}.html", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        reply_to=reply_to or [],
    )
    message.attach_alternative(html_body, "text/html")
    return message.send()


def _send_patient_message(appointment, *, event, title, introduction, action_label, action_url):
    booking_settings = get_booking_settings()
    reply_to = [booking_settings.notification_email] if booking_settings.notification_email else []
    context = _appointment_context(
        appointment,
        event=event,
        title=title,
        introduction=introduction,
        action_label=action_label,
        action_url=action_url,
    )
    return _send_email(
        subject=f"{title} — {_site_name()}",
        recipients=[appointment.email],
        template_name="appointment",
        context=context,
        reply_to=reply_to,
    )


def _send_manager_message(appointment, *, event, title):
    notification_email = get_booking_settings().notification_email
    if not notification_email:
        return 0
    return _send_email(
        subject=f"{title}: {appointment.patient_name}",
        recipients=[notification_email],
        template_name="manager",
        context=_appointment_context(appointment, event=event, title=title),
        reply_to=[appointment.email],
    )


def send_confirmation_notifications(appointment_id):
    appointment = Appointment.objects.select_related("service").get(pk=appointment_id)
    if appointment.confirmation_email_sent_at or appointment.status != Appointment.Status.CONFIRMED:
        return False

    _send_patient_message(
        appointment,
        event="confirmation",
        title="Wizyta potwierdzona",
        introduction="Płatność została przyjęta, a termin jest już zarezerwowany.",
        action_label="Zarządzaj wizytą",
        action_url=_appointment_context(appointment)["manage_url"],
    )
    _send_manager_message(
        appointment,
        event="confirmation",
        title="Nowa potwierdzona rezerwacja",
    )
    Appointment.objects.filter(
        pk=appointment.pk,
        confirmation_email_sent_at__isnull=True,
    ).update(confirmation_email_sent_at=timezone.now())
    return True


def send_reminder_notification(appointment_id):
    appointment = Appointment.objects.select_related("service").get(pk=appointment_id)
    if (
        appointment.reminder_email_sent_at
        or appointment.status != Appointment.Status.CONFIRMED
        or appointment.start_at <= timezone.now()
    ):
        return False

    _send_patient_message(
        appointment,
        event="reminder",
        title="Przypomnienie o wizycie",
        introduction="Przypominamy o zbliżającej się konsultacji.",
        action_label="Sprawdź szczegóły wizyty",
        action_url=_appointment_context(appointment)["manage_url"],
    )
    Appointment.objects.filter(
        pk=appointment.pk,
        reminder_email_sent_at__isnull=True,
    ).update(reminder_email_sent_at=timezone.now())
    return True


def send_cancellation_notifications(appointment_id):
    appointment = Appointment.objects.select_related("service").get(pk=appointment_id)
    if appointment.cancellation_email_sent_at or appointment.status != Appointment.Status.CANCELLED:
        return False

    _send_patient_message(
        appointment,
        event="cancellation",
        title="Wizyta anulowana",
        introduction="Termin został zwolniony. Możesz od razu wybrać nową datę konsultacji.",
        action_label="Wybierz nowy termin",
        action_url=_appointment_context(appointment)["new_booking_url"],
    )
    _send_manager_message(
        appointment,
        event="cancellation",
        title="Pacjent anulował wizytę",
    )
    Appointment.objects.filter(
        pk=appointment.pk,
        cancellation_email_sent_at__isnull=True,
    ).update(cancellation_email_sent_at=timezone.now())
    return True


def send_reschedule_notifications(appointment_id):
    appointment = Appointment.objects.select_related("service").get(pk=appointment_id)
    if appointment.reschedule_email_sent_at or appointment.status not in {
        Appointment.Status.PENDING,
        Appointment.Status.CONFIRMED,
    }:
        return False

    _send_patient_message(
        appointment,
        event="reschedule",
        title="Termin wizyty został zmieniony",
        introduction="Zmiana została zapisana. Płatność i pozostałe dane rezerwacji pozostają bez zmian.",
        action_label="Sprawdź nowy termin",
        action_url=_appointment_context(appointment)["manage_url"],
    )
    _send_manager_message(
        appointment,
        event="reschedule",
        title="Pacjent przełożył wizytę",
    )
    Appointment.objects.filter(
        pk=appointment.pk,
        reschedule_email_sent_at__isnull=True,
    ).update(reschedule_email_sent_at=timezone.now())
    return True


def send_due_reminders(now=None):
    now = now or timezone.now()
    reminder_deadline = now + timedelta(
        hours=get_booking_settings().reminder_hours_before
    )
    appointment_ids = Appointment.objects.filter(
        status=Appointment.Status.CONFIRMED,
        start_at__gt=now,
        start_at__lte=reminder_deadline,
        reminder_email_sent_at__isnull=True,
    ).values_list("pk", flat=True)

    sent = 0
    for appointment_id in appointment_ids.iterator():
        sent += int(send_reminder_notification(appointment_id))
    return sent
