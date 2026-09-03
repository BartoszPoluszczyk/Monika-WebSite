from datetime import datetime, time, timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Service

from .models import Appointment, BlockedTime, BookingSettings, WorkingHours
from .payments import mark_checkout_paid
from .services import get_available_slots, release_expired_payment_reservations


class BookingTestMixin:
    def setUp(self):
        self.service = Service.objects.create(
            name="Konsultacja indywidualna",
            duration_minutes=60,
            price=250,
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
            cancellation_notice_hours=24,
            reminder_hours_before=24,
            notification_email="monika@example.com",
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
        with (
            patch("booking.views.payments_configured", return_value=True),
            patch(
                "booking.views.create_checkout_session",
                return_value=SimpleNamespace(url="https://checkout.stripe.test/session"),
            ),
        ):
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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.test/session")
        self.assertEqual(appointment.patient_name, "Jan Kowalski")
        self.assertEqual(appointment.status, Appointment.Status.PENDING_PAYMENT)
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PENDING)
        self.assertEqual(appointment.payment_amount, self.service.price)

    def test_booking_is_not_created_before_stripe_is_configured(self):
        with patch("booking.views.payments_configured", return_value=False):
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
        self.assertEqual(Appointment.objects.count(), 0)
        self.assertContains(response, "Płatności testowe nie są jeszcze skonfigurowane")

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

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("booking:cancel", args=[appointment.public_id])
            )

        appointment.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("booking:confirmation", args=[appointment.public_id]),
        )
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.assertIsNotNone(appointment.cancellation_email_sent_at)
        self.assertEqual(len(mail.outbox), 2)

    def test_patient_cannot_cancel_inside_notice_period(self):
        appointment = Appointment.objects.create(
            service=self.service,
            start_at=timezone.now() + timedelta(hours=12),
            end_at=timezone.now() + timedelta(hours=13),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
            status=Appointment.Status.CONFIRMED,
        )

        response = self.client.post(
            reverse("booking:cancel", args=[appointment.public_id])
        )

        appointment.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

    def test_patient_can_reschedule_and_receives_email(self):
        appointment = Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
            status=Appointment.Status.CONFIRMED,
            payment_status=Appointment.PaymentStatus.PAID,
            payment_amount=self.service.price,
        )
        new_day = self.day + timedelta(days=7)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("booking:reschedule", args=[appointment.public_id]),
                {
                    "appointment_date": new_day.isoformat(),
                    "appointment_time": "10:00",
                },
            )

        appointment.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('booking:confirmation', args=[appointment.public_id])}?rescheduled=1",
        )
        self.assertEqual(timezone.localtime(appointment.start_at).date(), new_day)
        self.assertEqual(timezone.localtime(appointment.start_at).time(), time(10, 0))
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)
        self.assertIsNotNone(appointment.reschedule_email_sent_at)
        self.assertEqual(len(mail.outbox), 2)

    def test_calendar_file_can_be_downloaded(self):
        appointment = Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
            status=Appointment.Status.CONFIRMED,
        )

        response = self.client.get(
            reverse("booking:calendar_file", args=[appointment.public_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn(b"BEGIN:VCALENDAR", response.content)
        self.assertIn(str(appointment.public_id).encode(), response.content)


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


class PaymentLifecycleTests(BookingTestMixin, TestCase):
    def create_payment_appointment(self, expires_at=None):
        return Appointment.objects.create(
            service=self.service,
            start_at=self.aware(time(9, 0)),
            end_at=self.aware(time(10, 0)),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
            status=Appointment.Status.PENDING_PAYMENT,
            payment_status=Appointment.PaymentStatus.PENDING,
            payment_amount=self.service.price,
            payment_currency="PLN",
            payment_expires_at=expires_at or timezone.now() + timedelta(minutes=30),
            stripe_checkout_session_id="cs_test_123",
        )

    def test_paid_checkout_confirms_appointment(self):
        appointment = self.create_payment_appointment()

        session = {
            "id": "cs_test_123",
            "metadata": {"appointment_public_id": str(appointment.public_id)},
            "payment_status": "paid",
            "amount_total": int(self.service.price * 100),
            "currency": "pln",
            "payment_intent": "pi_test_123",
        }
        with self.captureOnCommitCallbacks(execute=True):
            changed = mark_checkout_paid(session)

        appointment.refresh_from_db()
        self.assertTrue(changed)
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)
        self.assertEqual(appointment.stripe_payment_intent_id, "pi_test_123")
        self.assertIsNotNone(appointment.paid_at)
        self.assertIsNotNone(appointment.confirmation_email_sent_at)
        self.assertEqual(len(mail.outbox), 2)

        with self.captureOnCommitCallbacks(execute=True):
            mark_checkout_paid(session)
        self.assertEqual(len(mail.outbox), 2)

    def test_expired_payment_releases_slot(self):
        appointment = self.create_payment_appointment(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        released = release_expired_payment_reservations()

        appointment.refresh_from_db()
        self.assertEqual(released, 1)
        self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.FAILED)

    def test_reminder_command_sends_each_reminder_once(self):
        start_at = timezone.now() + timedelta(hours=12)
        appointment = Appointment.objects.create(
            service=self.service,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="600700800",
            consent_privacy=True,
            status=Appointment.Status.CONFIRMED,
            payment_status=Appointment.PaymentStatus.PAID,
            payment_amount=self.service.price,
        )

        call_command("send_booking_reminders", stdout=StringIO())
        call_command("send_booking_reminders", stdout=StringIO())

        appointment.refresh_from_db()
        self.assertIsNotNone(appointment.reminder_email_sent_at)
        self.assertEqual(len(mail.outbox), 1)
