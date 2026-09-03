import calendar
from datetime import UTC, date, datetime
from functools import partial

import stripe
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from main.models import Service

from .emails import send_cancellation_notifications, send_reschedule_notifications
from .forms import AppointmentBookingForm, AppointmentRescheduleForm
from .models import Appointment
from .payments import (
    construct_webhook_event,
    create_checkout_session,
    expire_checkout_for_appointment,
    mark_checkout_failed,
    mark_checkout_paid,
    payments_configured,
    retrieve_and_sync_checkout,
)
from .services import (
    can_patient_manage,
    can_patient_reschedule,
    create_appointment,
    get_available_slots,
    get_booking_settings,
    reschedule_existing_appointment,
)


MONTH_NAMES = (
    "",
    "Styczeń",
    "Luty",
    "Marzec",
    "Kwiecień",
    "Maj",
    "Czerwiec",
    "Lipiec",
    "Sierpień",
    "Wrzesień",
    "Październik",
    "Listopad",
    "Grudzień",
)


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _parse_month(value, fallback):
    try:
        parsed = datetime.strptime(value, "%Y-%m").date()
        return parsed.replace(day=1)
    except (TypeError, ValueError):
        return fallback.replace(day=1)


def _shift_month(month, offset):
    absolute_month = month.year * 12 + month.month - 1 + offset
    return date(absolute_month // 12, absolute_month % 12 + 1, 1)


def _calendar_context(
    service,
    displayed_month,
    selected_date,
    exclude_appointment=None,
):
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
        displayed_month.year,
        displayed_month.month,
    ):
        days = []
        for day in week:
            is_current_month = day.month == displayed_month.month
            slots = (
                get_available_slots(
                    service,
                    day,
                    exclude_appointment=exclude_appointment,
                )
                if is_current_month
                else []
            )
            if exclude_appointment:
                slots = [slot for slot in slots if slot != exclude_appointment.start_at]
            available = bool(slots)
            days.append(
                {
                    "date": day,
                    "is_current_month": is_current_month,
                    "is_available": available,
                    "is_selected": day == selected_date,
                    "is_today": day == timezone.localdate(),
                }
            )
        weeks.append(days)
    return weeks


def book_appointment(request):
    services = Service.objects.filter(
        is_active=True,
        duration_minutes__isnull=False,
        price__isnull=False,
    ).order_by("order")

    service_id = request.POST.get("service") or request.GET.get("service")
    service = None
    if service_id:
        service = get_object_or_404(services, pk=service_id)

    selected_date = _parse_date(request.POST.get("appointment_date") or request.GET.get("date"))
    default_month = selected_date or timezone.localdate()
    displayed_month = _parse_month(request.GET.get("month"), default_month)
    available_slots = get_available_slots(service, selected_date) if service and selected_date else []

    form = None
    if service and selected_date:
        form = AppointmentBookingForm(
            request.POST or None,
            available_slots=available_slots,
            initial={"appointment_date": selected_date},
        )
        if request.method == "POST" and form.is_valid():
            if not payments_configured():
                form.add_error(
                    None,
                    "Płatności testowe nie są jeszcze skonfigurowane. Dodaj klucze Stripe i uruchom serwer ponownie.",
                )
            else:
                appointment = None
                try:
                    appointment = create_appointment(
                        service=service,
                        day=form.cleaned_data["appointment_date"],
                        start_time=datetime.strptime(
                            form.cleaned_data["appointment_time"],
                            "%H:%M",
                        ).time(),
                        payment_required=True,
                        first_name=form.cleaned_data["first_name"],
                        last_name=form.cleaned_data["last_name"],
                        email=form.cleaned_data["email"],
                        phone=form.cleaned_data["phone"],
                        visit_type=form.cleaned_data["visit_type"],
                        notes=form.cleaned_data["notes"],
                        consent_privacy=form.cleaned_data["consent_privacy"],
                    )
                    checkout_session = create_checkout_session(appointment, request)
                except ValidationError as error:
                    form.add_error("appointment_time", " ".join(error.messages))
                    available_slots = get_available_slots(service, selected_date)
                except (ImproperlyConfigured, stripe.StripeError):
                    if appointment:
                        appointment.status = Appointment.Status.CANCELLED
                        appointment.payment_status = Appointment.PaymentStatus.FAILED
                        appointment.save(
                            update_fields=["status", "payment_status", "updated_at"]
                        )
                    form.add_error(
                        None,
                        "Nie udało się uruchomić bezpiecznej płatności. Spróbuj ponownie za chwilę.",
                    )
                    available_slots = get_available_slots(service, selected_date)
                else:
                    return redirect(checkout_session.url)

    calendar_weeks = _calendar_context(service, displayed_month, selected_date) if service else []
    previous_month = _shift_month(displayed_month, -1)
    next_month = _shift_month(displayed_month, 1)

    return render(
        request,
        "booking/book.html",
        {
            "services": services,
            "selected_service": service,
            "selected_date": selected_date,
            "available_slots": available_slots,
            "form": form,
            "calendar_weeks": calendar_weeks,
            "displayed_month": displayed_month,
            "month_label": f"{MONTH_NAMES[displayed_month.month]} {displayed_month.year}",
            "previous_month": previous_month.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
            "payments_configured": payments_configured(),
        },
    )


def booking_confirmation(request, public_id):
    appointment = get_object_or_404(Appointment, public_id=public_id)
    session_id = request.GET.get("session_id")
    if (
        session_id
        and session_id == appointment.stripe_checkout_session_id
        and payments_configured()
    ):
        try:
            retrieve_and_sync_checkout(session_id)
        except stripe.StripeError:
            pass
        appointment.refresh_from_db()
    booking_settings = get_booking_settings()
    return render(
        request,
        "booking/confirmation.html",
        {
            "appointment": appointment,
            "can_cancel": can_patient_manage(appointment),
            "can_reschedule": can_patient_reschedule(appointment),
            "cancellation_notice_hours": booking_settings.cancellation_notice_hours,
            "rescheduled": request.GET.get("rescheduled") == "1",
        },
    )


def payment_cancelled(request, public_id):
    appointment = get_object_or_404(Appointment, public_id=public_id)
    if (
        appointment.status == Appointment.Status.PENDING_PAYMENT
        and appointment.payment_status == Appointment.PaymentStatus.PENDING
    ):
        expire_checkout_for_appointment(appointment)
        appointment.status = Appointment.Status.CANCELLED
        appointment.payment_status = Appointment.PaymentStatus.FAILED
        appointment.save(update_fields=["status", "payment_status", "updated_at"])
    return render(request, "booking/payment_cancelled.html", {"appointment": appointment})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = construct_webhook_event(
            request.body,
            request.headers.get("Stripe-Signature", ""),
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)
    except ImproperlyConfigured:
        return HttpResponse(status=503)

    event_type = event["type"]
    checkout_session = event["data"]["object"]
    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        mark_checkout_paid(checkout_session)
    elif event_type in {
        "checkout.session.expired",
        "checkout.session.async_payment_failed",
    }:
        mark_checkout_failed(checkout_session)

    return HttpResponse(status=200)


def cancel_appointment(request, public_id):
    appointment = get_object_or_404(Appointment, public_id=public_id)
    can_cancel = can_patient_manage(appointment)

    if request.method == "POST":
        if not can_cancel:
            raise Http404
        if appointment.status == Appointment.Status.PENDING_PAYMENT:
            expire_checkout_for_appointment(appointment)
            appointment.payment_status = Appointment.PaymentStatus.FAILED
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "payment_status", "updated_at"])
        transaction.on_commit(
            partial(send_cancellation_notifications, appointment.pk),
            robust=True,
        )
        return redirect("booking:confirmation", public_id=appointment.public_id)

    return render(
        request,
        "booking/cancel.html",
        {
            "appointment": appointment,
            "can_cancel": can_cancel,
            "cancellation_notice_hours": get_booking_settings().cancellation_notice_hours,
        },
    )


def reschedule_appointment(request, public_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("service"),
        public_id=public_id,
    )
    can_reschedule = can_patient_reschedule(appointment)
    selected_date = _parse_date(
        request.POST.get("appointment_date") or request.GET.get("date")
    )
    default_month = selected_date or timezone.localdate()
    displayed_month = _parse_month(request.GET.get("month"), default_month)
    available_slots = (
        get_available_slots(
            appointment.service,
            selected_date,
            exclude_appointment=appointment,
        )
        if can_reschedule and selected_date
        else []
    )
    available_slots = [
        slot for slot in available_slots if slot != appointment.start_at
    ]

    form = None
    if can_reschedule and selected_date:
        form = AppointmentRescheduleForm(
            request.POST or None,
            available_slots=available_slots,
            initial={"appointment_date": selected_date},
        )
        if request.method == "POST" and form.is_valid():
            try:
                appointment = reschedule_existing_appointment(
                    appointment=appointment,
                    day=form.cleaned_data["appointment_date"],
                    start_time=datetime.strptime(
                        form.cleaned_data["appointment_time"],
                        "%H:%M",
                    ).time(),
                )
            except ValidationError as error:
                form.add_error("appointment_time", " ".join(error.messages))
            else:
                transaction.on_commit(
                    partial(send_reschedule_notifications, appointment.pk),
                    robust=True,
                )
                confirmation_url = reverse(
                    "booking:confirmation",
                    args=[appointment.public_id],
                )
                return redirect(f"{confirmation_url}?rescheduled=1")

    calendar_weeks = (
        _calendar_context(
            appointment.service,
            displayed_month,
            selected_date,
            exclude_appointment=appointment,
        )
        if can_reschedule
        else []
    )
    return render(
        request,
        "booking/reschedule.html",
        {
            "appointment": appointment,
            "can_reschedule": can_reschedule,
            "selected_date": selected_date,
            "available_slots": available_slots,
            "form": form,
            "calendar_weeks": calendar_weeks,
            "displayed_month": displayed_month,
            "month_label": f"{MONTH_NAMES[displayed_month.month]} {displayed_month.year}",
            "previous_month": _shift_month(displayed_month, -1).strftime("%Y-%m"),
            "next_month": _shift_month(displayed_month, 1).strftime("%Y-%m"),
            "cancellation_notice_hours": get_booking_settings().cancellation_notice_hours,
        },
    )


def _escape_ics(value):
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@require_GET
def appointment_calendar_file(request, public_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("service"),
        public_id=public_id,
    )
    if appointment.status not in {Appointment.Status.PENDING, Appointment.Status.CONFIRMED}:
        raise Http404

    start_utc = appointment.start_at.astimezone(UTC)
    end_utc = appointment.end_at.astimezone(UTC)
    stamp_utc = timezone.now().astimezone(UTC)
    content = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Dietetyk Monika//Rezerwacje//PL",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:{appointment.public_id}@dietetyk-monika",
            f"DTSTAMP:{stamp_utc:%Y%m%dT%H%M%SZ}",
            f"DTSTART:{start_utc:%Y%m%dT%H%M%SZ}",
            f"DTEND:{end_utc:%Y%m%dT%H%M%SZ}",
            f"SUMMARY:{_escape_ics(appointment.service.name)} — Dietetyk Monika",
            f"DESCRIPTION:{_escape_ics(f'Forma wizyty: {appointment.get_visit_type_display()}')}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]
    )
    response = HttpResponse(content, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="wizyta-{appointment.start_at:%Y-%m-%d}.ics"'
    )
    return response
