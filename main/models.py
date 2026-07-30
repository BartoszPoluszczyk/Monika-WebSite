from django.db import models


class AboutPage(models.Model):
    title = models.CharField(
        max_length=150,
        default="O mnie",
        verbose_name="Tytuł",
    )

    subtitle = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Krótki nagłówek",
        help_text="Krótki tekst wyświetlany pod głównym tytułem.",
    )

    description = models.TextField(
        verbose_name="Opis",
    )

    photo = models.ImageField(
        upload_to="about/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Strona O mnie"
        verbose_name_plural = "Strona O mnie"


class Specialization(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Nazwa specjalizacji",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specjalizacja"
        verbose_name_plural = "Specjalizacje"
        ordering = ["name"]