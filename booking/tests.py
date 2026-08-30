from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Service

from .models import Appointment, BlockedTime, BookingSettings, WorkingHours
from .services import get_available_slots


class BookingTestMixin:
    def setUp(self):
        self.service = Service.objects.create(
            name="Konsultacja indywidualna",
            duration_minutes=60,
            is_active=True,
        )
        self.day = timezone.localdate() + timedelta(days=3)
        WorkingHours.objects.create(
            weekday=self.day.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        BookingSettings.objects.create(
            slot_interval_minutes=30,
            buffer_minutes=15,
            minimum_notice_hours=0,
            booking_window_days=90,
        )

    def aware(self, value):
        return timezone.make_aware(
            datetime.combine(self.day, value),
            timezone.get_current_timezone(),
        )


class AvailableSlotsTests(BookingTestMixin, TestCase):
    def test_slots_are_generated_from_working_hours(self):
        slots = get_available_slots(self.service, self.day)

        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots],
            ["09:00", "09:30", "10:00", "10:30", "11:00"],
        )

    def test_existing_appointment_and_buffer_remove_conflicting_slots(self):
        Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Anna",
            last_name="Nowak",
            email="anna@example.com",
            phone="500600700",
            consent_privacy=True,
        )

        slots = get_available_slots(self.service, self.day)

        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots],
            ["10:30", "11:00"],
        )

    def test_all_day_block_removes_all_slots(self):
        BlockedTime.objects.create(date=self.day, reason="Urlop")

        self.assertEqual(get_available_slots(self.service, self.day), [])


class PublicBookingTests(BookingTestMixin, TestCase):
    def test_booking_calendar_page_renders(self):
        response = self.client.get(
            reverse("booking:book"),
            {"service": self.service.pk, "month": self.day.strftime("%Y-%m")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wybierz dzień")
        self.assertContains(response, self.service.name)

    def test_patient_can_book_available_slot(self):
        response = self.client.post(
            reverse("booking:book"),
            {
                "service": self.service.pk,
                "appointment_date": self.day.isoformat(),
                "appointment_time": "09:00",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "email": "jan@example.com",
                "phone": "600700800",
                "visit_type": Appointment.VisitType.ONLINE,
                "notes": "",
                "consent_privacy": "on",
            },
        )

        appointment = Appointment.objects.get()
        self.assertRedirects(
            response,
            reverse("booking:confirmation", args=[appointment.public_id]),
        )
        self.assertEqual(appointment.patient_name, "Jan Kowalski")

    def test_taken_slot_cannot_be_booked_again(self):
        Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Anna",
            last_name="Nowak",
            email="anna@example.com",
            phone="500600700",
            consent_privacy=True,
        )

        response = self.client.post(
            reverse("booking:book"),
            {
                "service": self.service.pk,
                "appointment_date": self.day.isoformat(),
                "appointment_time": "09:00",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "email": "jan@example.com",
                "phone": "600700800",
                "visit_type": Appointment.VisitType.ONLINE,
                "notes": "",
                "consent_privacy": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertContains(response, "Wybierz poprawną wartość")

    def test_patient_can_cancel_future_appointment(self):
        appointment = Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
        )

        response = self.client.post(
            reverse("booking:cancel", args=[appointment.public_id])
        )

        appointment.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("booking:confirmation", args=[appointment.public_id]),
        )
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)


class AppointmentAdminTests(BookingTestMixin, TestCase):
    def test_calendar_is_available_to_admin(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:booking_appointment_calendar"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kalendarz wizyt")
