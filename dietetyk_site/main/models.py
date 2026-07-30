from django.db import models


class Specialization(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Nazwa specjalizacji"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specjalizacja"
        verbose_name_plural = "Specjalizacje"