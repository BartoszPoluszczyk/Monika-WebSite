import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class BookingSettings(models.Model):
    slot_interval_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Odstęp między możliwymi godzinami rozpoczęcia",
        help_text="Na przykład 15 pozwala wyświetlić terminy 09:00, 09:15, 09:30 itd.",
    )
    buffer_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Przerwa między wizytami (minuty)",
    )
    minimum_notice_hours = models.PositiveIntegerField(
        default=24,
        verbose_name="Minimalne wyprzedzenie rezerwacji (godziny)",
    )
    booking_window_days = models.PositiveIntegerField(
        default=90,
        verbose_name="Maksymalny okres rezerwacji (dni)",
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Ustawienia rezerwacji"

    class Meta:
        verbose_name = "Ustawienia rezerwacji"
        verbose_name_plural = "Ustawienia rezerwacji"


class WorkingHours(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Poniedziałek"
        TUESDAY = 1, "Wtorek"
        WEDNESDAY = 2, "Środa"
        THURSDAY = 3, "Czwartek"
        FRIDAY = 4, "Piątek"
        SATURDAY = 5, "Sobota"
        SUNDAY = 6, "Niedziela"

    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        verbose_name="Dzień tygodnia",
    )
    start_time = models.TimeField(verbose_name="Od godziny")
    end_time = models.TimeField(verbose_name="Do godziny")
    is_active = models.BooleanField(default=True, verbose_name="Aktywne")

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "Godzina zakończenia musi być późniejsza niż rozpoczęcia."})

    def __str__(self):
        return f"{self.get_weekday_display()}: {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    class Meta:
        verbose_name = "Godziny pracy"
        verbose_name_plural = "Godziny pracy"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["weekday", "start_time", "end_time"],
                name="unique_working_hours_period",
            ),
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="working_hours_end_after_start",
            ),
        ]


class BlockedTime(models.Model):
    date = models.DateField(verbose_name="Data")
    start_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Od godziny",
        help_text="Pozostaw obie godziny puste, aby zablokować cały dzień.",
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Do godziny",
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Powód / notatka",
    )

    @property
    def is_all_day(self):
        return self.start_time is None and self.end_time is None

    def clean(self):
        one_time_missing = (self.start_time is None) != (self.end_time is None)
        if one_time_missing:
            raise ValidationError("Podaj obie godziny albo pozostaw obie puste.")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "Godzina zakończenia musi być późniejsza niż rozpoczęcia."})

    def __str__(self):
        if self.is_all_day:
            return f"{self.date:%d.%m.%Y} — cały dzień"
        return f"{self.date:%d.%m.%Y}: {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    class Meta:
        verbose_name = "Zablokowany termin"
        verbose_name_plural = "Zablokowane terminy i dni wolne"
        ordering = ["date", "start_time"]


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Oczekuje"
        CONFIRMED = "confirmed", "Potwierdzona"
        COMPLETED = "completed", "Odbyta"
        CANCELLED = "cancelled", "Anulowana"
        NO_SHOW = "no_show", "Nieobecność"

    class VisitType(models.TextChoices):
        ONLINE = "online", "Online"
        IN_PERSON = "in_person", "Stacjonarnie"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    service = models.ForeignKey(
        "main.Service",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Usługa",
    )
    start_at = models.DateTimeField(verbose_name="Początek wizyty")
    end_at = models.DateTimeField(verbose_name="Koniec wizyty")
    visit_type = models.CharField(
        max_length=20,
        choices=VisitType.choices,
        default=VisitType.ONLINE,
        verbose_name="Forma wizyty",
    )
    first_name = models.CharField(max_length=100, verbose_name="Imię")
    last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
    email = models.EmailField(verbose_name="Adres e-mail")
    phone = models.CharField(max_length=30, verbose_name="Numer telefonu")
    notes = models.TextField(
        blank=True,
        verbose_name="Krótka wiadomość",
        help_text="Nie wpisuj tutaj szczegółowych informacji medycznych.",
    )
    consent_privacy = models.BooleanField(
        default=False,
        verbose_name="Zgoda na przetwarzanie danych w celu obsługi rezerwacji",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    @property
    def patient_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def duration_minutes(self):
        return int((self.end_at - self.start_at).total_seconds() // 60)

    def clean(self):
        errors = {}
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            errors["end_at"] = "Koniec wizyty musi przypadać po jej rozpoczęciu."
        if not self.consent_privacy:
            errors["consent_privacy"] = "Zgoda jest wymagana do zapisania rezerwacji."

        if self.start_at and self.end_at and self.status in self.active_statuses():
            overlap = Appointment.objects.filter(
                status__in=self.active_statuses(),
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
            )
            if self.pk:
                overlap = overlap.exclude(pk=self.pk)
            if overlap.exists():
                errors["start_at"] = "Ten termin koliduje z inną aktywną wizytą."

        if errors:
            raise ValidationError(errors)

    @classmethod
    def active_statuses(cls):
        return [cls.Status.PENDING, cls.Status.CONFIRMED]

    def __str__(self):
        return f"{self.start_at:%d.%m.%Y %H:%M} — {self.patient_name}"

    class Meta:
        verbose_name = "Wizyta"
        verbose_name_plural = "Wizyty"
        ordering = ["start_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")),
                name="appointment_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["start_at"],
                condition=Q(status__in=["pending", "confirmed"]),
                name="unique_active_appointment_start",
            ),
        ]
