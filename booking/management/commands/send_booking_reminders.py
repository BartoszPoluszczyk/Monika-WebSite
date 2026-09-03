from django.core.management.base import BaseCommand

from booking.emails import send_due_reminders


class Command(BaseCommand):
    help = "Wysyła przypomnienia o potwierdzonych wizytach, które zbliżają się do terminu."

    def handle(self, *args, **options):
        sent = send_due_reminders()
        self.stdout.write(self.style.SUCCESS(f"Wysłane przypomnienia: {sent}"))
