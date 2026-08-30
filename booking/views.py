import calendar
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from main.models import Service

from .forms import AppointmentBookingForm
from .models import Appointment
from .services import create_appointment, get_available_slots


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


def _calendar_context(service, displayed_month, selected_date):
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
        displayed_month.year,
        displayed_month.month,
    ):
        days = []
        for day in week:
            is_current_month = day.month == displayed_month.month
            available = bool(get_available_slots(service, day)) if is_current_month else False
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
            try:
                appointment = create_appointment(
                    service=service,
                    day=form.cleaned_data["appointment_date"],
                    start_time=datetime.strptime(
                        form.cleaned_data["appointment_time"],
                        "%H:%M",
                    ).time(),
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    visit_type=form.cleaned_data["visit_type"],
                    notes=form.cleaned_data["notes"],
                    consent_privacy=form.cleaned_data["consent_privacy"],
                )
            except ValidationError as error:
                form.add_error("appointment_time", error.message)
                available_slots = get_available_slots(service, selected_date)
            else:
                return redirect("booking:confirmation", public_id=appointment.public_id)

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
        },
    )


def booking_confirmation(request, public_id):
    appointment = get_object_or_404(Appointment, public_id=public_id)
    return render(request, "booking/confirmation.html", {"appointment": appointment})


def cancel_appointment(request, public_id):
    appointment = get_object_or_404(Appointment, public_id=public_id)
    can_cancel = (
        appointment.status in Appointment.active_statuses()
        and appointment.start_at > timezone.now()
    )

    if request.method == "POST":
        if not can_cancel:
            raise Http404
        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])
        return redirect("booking:confirmation", public_id=appointment.public_id)

    return render(
        request,
        "booking/cancel.html",
        {"appointment": appointment, "can_cancel": can_cancel},
    )
