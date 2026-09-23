from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from main.models import Service

from .emails import send_confirmation_notifications
from .models import Appointment


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class LegalConfirmationEmailTests(TestCase):
    def test_confirmation_attaches_accepted_documents(self):
        service = Service.objects.create(
            name="Konsultacja",
            duration_minutes=60,
            price=250,
            is_active=True,
        )
        appointment = Appointment.objects.create(
            service=service,
            start_at=timezone.now() + timedelta(days=5),
            end_at=timezone.now() + timedelta(days=5, hours=1),
            first_name="Jan",
            last_name="Kowalski",
            email="jan@example.com",
            phone="500600700",
            consent_privacy=True,
            terms_accepted=True,
            terms_accepted_at=timezone.now(),
            terms_version="1.0",
            terms_snapshot="Treść regulaminu",
            privacy_acknowledged_at=timezone.now(),
            privacy_version="1.0",
            privacy_snapshot="Treść polityki",
            status=Appointment.Status.CONFIRMED,
            payment_status=Appointment.PaymentStatus.PAID,
        )

        self.assertTrue(send_confirmation_notifications(appointment.pk))

        names = {attachment[0] for attachment in mail.outbox[0].attachments}
        self.assertIn("regulamin-1.0.txt", names)
        self.assertIn("polityka-prywatnosci-1.0.txt", names)
