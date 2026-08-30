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


def get_available_slots(service, day, now=None):
    if not service or not service.duration_minutes:
        return []

    booking_settings = get_booking_settings()
    now = timezone.localtime(now or timezone.now())
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
    appointments = list(
        Appointment.objects.filter(
            status__in=Appointment.active_statuses(),
            start_at__lt=day_end,
            end_at__gt=day_start,
        )
    )

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


def create_appointment(*, service, day, start_time, **patient_data):
    start_at = _aware_datetime(day, start_time)
    end_at = start_at + timedelta(minutes=service.duration_minutes)

    try:
        with transaction.atomic():
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
                **patient_data,
            )
            appointment.full_clean()
            appointment.save()
            return appointment
    except IntegrityError as error:
        raise ValidationError("Wybrany termin został właśnie zarezerwowany. Wybierz inną godzinę.") from error
