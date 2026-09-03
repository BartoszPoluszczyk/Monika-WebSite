from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Appointment, BlockedTime, BookingSettings, WorkingHours


def get_booking_settings():
    settings, _ = BookingSettings.objects.get_or_create(pk=1)
    return settings


def _aware_datetime(day, value):
    naive_value = datetime.combine(day, value)
    return timezone.make_aware(naive_value, timezone.get_current_timezone())


def release_expired_payment_reservations(now=None):
    now = now or timezone.now()
    return Appointment.objects.filter(
        status=Appointment.Status.PENDING_PAYMENT,
        payment_status=Appointment.PaymentStatus.PENDING,
        payment_expires_at__lte=now,
    ).update(
        status=Appointment.Status.CANCELLED,
        payment_status=Appointment.PaymentStatus.FAILED,
    )


def get_available_slots(service, day, now=None, exclude_appointment=None):
    if not service or not service.duration_minutes:
        return []

    booking_settings = get_booking_settings()
    now = timezone.localtime(now or timezone.now())
    release_expired_payment_reservations(now)
    today = now.date()
    last_bookable_day = today + timedelta(days=booking_settings.booking_window_days)

    if day < today or day > last_bookable_day:
        return []

    working_periods = WorkingHours.objects.filter(
        weekday=day.weekday(),
        is_active=True,
    )
    if not working_periods.exists():
        return []

    blocked_periods = list(BlockedTime.objects.filter(date=day))
    if any(block.is_all_day for block in blocked_periods):
        return []

    day_start = _aware_datetime(day, datetime.min.time())
    day_end = day_start + timedelta(days=1)
    appointment_query = Appointment.objects.filter(
        status__in=Appointment.active_statuses(),
        start_at__lt=day_end,
        end_at__gt=day_start,
    )
    if exclude_appointment:
        appointment_query = appointment_query.exclude(pk=exclude_appointment.pk)
    appointments = list(appointment_query)

    duration = timedelta(minutes=service.duration_minutes)
    interval = timedelta(minutes=max(1, booking_settings.slot_interval_minutes))
    buffer = timedelta(minutes=booking_settings.buffer_minutes)
    earliest_start = now + timedelta(hours=booking_settings.minimum_notice_hours)
    slots = []

    for period in working_periods:
        candidate = _aware_datetime(day, period.start_time)
        period_end = _aware_datetime(day, period.end_time)

        while candidate + duration <= period_end:
            candidate_end = candidate + duration
            is_after_notice = candidate >= earliest_start
            conflicts_with_block = any(
                candidate < _aware_datetime(day, block.end_time)
                and candidate_end > _aware_datetime(day, block.start_time)
                for block in blocked_periods
                if not block.is_all_day
            )
            conflicts_with_appointment = any(
                candidate < appointment.end_at + buffer
                and candidate_end + buffer > appointment.start_at
                for appointment in appointments
            )

            if is_after_notice and not conflicts_with_block and not conflicts_with_appointment:
                slots.append(candidate)

            candidate += interval

    return sorted(set(slots))


def create_appointment(*, service, day, start_time, payment_required=False, **patient_data):
    start_at = _aware_datetime(day, start_time)
    end_at = start_at + timedelta(minutes=service.duration_minutes)
    booking_settings = get_booking_settings()
    payment_hold_minutes = max(30, booking_settings.payment_hold_minutes) + 1

    if payment_required and service.price is None:
        raise ValidationError("Ta usługa nie ma ustawionej ceny i nie może zostać opłacona online.")

    try:
        with transaction.atomic():
            release_expired_payment_reservations()
            list(
                Appointment.objects.select_for_update().filter(
                    status__in=Appointment.active_statuses(),
                    start_at__lt=end_at,
                    end_at__gt=start_at,
                )
            )
            if start_at not in get_available_slots(service, day):
                raise ValidationError("Wybrany termin nie jest już dostępny. Wybierz inną godzinę.")

            appointment = Appointment(
                service=service,
                start_at=start_at,
                end_at=end_at,
                status=(
                    Appointment.Status.PENDING_PAYMENT
                    if payment_required
                    else Appointment.Status.PENDING
                ),
                payment_status=(
                    Appointment.PaymentStatus.PENDING
                    if payment_required
                    else Appointment.PaymentStatus.NOT_REQUIRED
                ),
                payment_amount=service.price if payment_required else None,
                payment_expires_at=(
                    timezone.now() + timedelta(minutes=payment_hold_minutes)
                    if payment_required
                    else None
                ),
                **patient_data,
            )
            appointment.full_clean()
            appointment.save()
            return appointment
    except IntegrityError as error:
        raise ValidationError("Wybrany termin został właśnie zarezerwowany. Wybierz inną godzinę.") from error


def can_patient_manage(appointment, now=None):
    now = now or timezone.now()
    booking_settings = get_booking_settings()
    deadline = appointment.start_at - timedelta(
        hours=booking_settings.cancellation_notice_hours
    )
    return (
        appointment.status in Appointment.active_statuses()
        and now < deadline
    )


def can_patient_reschedule(appointment, now=None):
    return (
        appointment.status in {Appointment.Status.PENDING, Appointment.Status.CONFIRMED}
        and can_patient_manage(appointment, now=now)
    )


def reschedule_existing_appointment(*, appointment, day, start_time):
    try:
        with transaction.atomic():
            appointment = (
                Appointment.objects.select_for_update()
                .select_related("service")
                .get(pk=appointment.pk)
            )
            if not can_patient_reschedule(appointment):
                raise ValidationError(
                    "Tej wizyty nie można już przełożyć przez stronę."
                )

            start_at = _aware_datetime(day, start_time)
            end_at = start_at + timedelta(minutes=appointment.service.duration_minutes)
            if start_at == appointment.start_at:
                raise ValidationError("Wybierz termin inny niż obecny.")

            list(
                Appointment.objects.select_for_update()
                .filter(
                    status__in=Appointment.active_statuses(),
                    start_at__lt=end_at,
                    end_at__gt=start_at,
                )
                .exclude(pk=appointment.pk)
            )
            available_slots = get_available_slots(
                appointment.service,
                day,
                exclude_appointment=appointment,
            )
            if start_at not in available_slots:
                raise ValidationError(
                    "Wybrany termin nie jest już dostępny. Wybierz inną godzinę."
                )

            appointment.previous_start_at = appointment.start_at
            appointment.start_at = start_at
            appointment.end_at = end_at
            appointment.rescheduled_at = timezone.now()
            appointment.reschedule_email_sent_at = None
            appointment.reminder_email_sent_at = None
            appointment.full_clean()
            appointment.save(
                update_fields=[
                    "previous_start_at",
                    "start_at",
                    "end_at",
                    "rescheduled_at",
                    "reschedule_email_sent_at",
                    "reminder_email_sent_at",
                    "updated_at",
                ]
            )
            return appointment
    except IntegrityError as error:
        raise ValidationError(
            "Wybrany termin został właśnie zajęty. Wybierz inną godzinę."
        ) from error
