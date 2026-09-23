from django.core.management.base import BaseCommand

from main.newsletter import send_due_campaigns


class Command(BaseCommand):
    help = "Wysyła gotowe kampanie newsletterowe, których termin już nadszedł."

    def handle(self, *args, **options):
        results = send_due_campaigns()
        if not results:
            self.stdout.write("Brak kampanii oczekujących na wysyłkę.")
            return

        for campaign_id, sent_count, failed_count in results:
            self.stdout.write(
                self.style.SUCCESS(
                    (
                        f"Kampania {campaign_id}: wysłano {sent_count}, "
                        f"błędy {failed_count}."
                    )
                )
            )
