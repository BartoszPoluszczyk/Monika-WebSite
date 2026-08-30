import calendar
from datetime import date, datetime

from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.utils import timezone

from .models import Appointment, BlockedTime, BookingSettings, WorkingHours


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


def _parse_month(value):
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        return timezone.localdate().replace(day=1)


def _shift_month(month, offset):
    absolute_month = month.year * 12 + month.month - 1 + offset
    return date(absolute_month // 12, absolute_month % 12 + 1, 1)


@admin.register(BookingSettings)
class BookingSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Dostępność terminów",
            {
                "fields": (
                    "slot_interval_minutes",
                    "buffer_minutes",
                    "minimum_notice_hours",
                    "booking_window_days",
                    "payment_hold_minutes",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        return not BookingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ("weekday", "start_time", "end_time", "is_active")
    list_editable = ("start_time", "end_time", "is_active")
    list_filter = ("weekday", "is_active")
    ordering = ("weekday", "start_time")


@admin.register(BlockedTime)
class BlockedTimeAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "whole_day", "reason")
    list_filter = ("date",)
    search_fields = ("reason",)
    date_hierarchy = "date"

    @admin.display(boolean=True, description="Cały dzień")
    def whole_day(self, obj):
        return obj.is_all_day


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    change_list_template = "admin/booking/appointment/change_list.html"
    list_display = (
        "appointment_date",
        "appointment_time",
        "patient_name",
        "service",
        "visit_type",
        "status",
        "payment_status",
        "payment_amount",
        "phone",
    )
    list_filter = ("status", "payment_status", "visit_type", "service", "start_at")
    search_fields = ("first_name", "last_name", "email", "phone")
    ordering = ("start_at",)
    date_hierarchy = "start_at"
    readonly_fields = (
        "public_id",
        "payment_status",
        "payment_amount",
        "payment_currency",
        "payment_expires_at",
        "paid_at",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Termin", {"fields": ("service", "start_at", "end_at", "visit_type", "status")}),
        ("Pacjent", {"fields": ("first_name", "last_name", "email", "phone")}),
        ("Informacje dodatkowe", {"fields": ("notes", "consent_privacy")}),
        (
            "Płatność online",
            {
                "fields": (
                    "payment_status",
                    "payment_amount",
                    "payment_currency",
                    "payment_expires_at",
                    "paid_at",
                    "stripe_checkout_session_id",
                    "stripe_payment_intent_id",
                )
            },
        ),
        ("Dane techniczne", {"fields": ("public_id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Data", ordering="start_at")
    def appointment_date(self, obj):
        return timezone.localtime(obj.start_at).strftime("%d.%m.%Y")

    @admin.display(description="Godzina", ordering="start_at")
    def appointment_time(self, obj):
        return timezone.localtime(obj.start_at).strftime("%H:%M")

    def get_urls(self):
        return [
            path(
                "kalendarz/",
                self.admin_site.admin_view(self.calendar_view),
                name="booking_appointment_calendar",
            )
        ] + super().get_urls()

    def calendar_view(self, request):
        displayed_month = _parse_month(request.GET.get("month"))
        next_month = _shift_month(displayed_month, 1)
        previous_month = _shift_month(displayed_month, -1)
        month_end = next_month

        appointments = Appointment.objects.filter(
            start_at__date__gte=displayed_month,
            start_at__date__lt=month_end,
        ).select_related("service")

        appointments_by_day = {}
        for appointment in appointments:
            local_day = timezone.localtime(appointment.start_at).date()
            appointments_by_day.setdefault(local_day, []).append(appointment)

        calendar_weeks = []
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
            displayed_month.year,
            displayed_month.month,
        ):
            calendar_weeks.append(
                [
                    {
                        "date": day,
                        "is_current_month": day.month == displayed_month.month,
                        "is_today": day == timezone.localdate(),
                        "appointments": appointments_by_day.get(day, []),
                    }
                    for day in week
                ]
            )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": f"Kalendarz wizyt — {MONTH_NAMES[displayed_month.month]} {displayed_month.year}",
            "calendar_weeks": calendar_weeks,
            "previous_month": previous_month.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
        }
        return render(request, "admin/booking/appointment/calendar.html", context)
