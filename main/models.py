from django.db import models


class SiteSettings(models.Model):
    logo = models.ImageField(
        upload_to="branding/",
        blank=True,
        null=True,
        verbose_name="Logo",
    )

    site_name = models.CharField(
        max_length=150,
        default="Dietetyk Monika",
        verbose_name="Nazwa strony",
    )

    def __str__(self):
        return "Ustawienia strony"

    class Meta:
        verbose_name = "Ustawienia strony"
        verbose_name_plural = "Ustawienia strony"

class HomePage(models.Model):
    hero_eyebrow = models.CharField(
        max_length=150,
        default="Dietetyka dopasowana do Ciebie",
        verbose_name="Mały nagłówek Hero",
    )

    hero_title = models.CharField(
        max_length=250,
        default="Zdrowie zaczyna się od dobrych wyborów",
        verbose_name="Główny nagłówek Hero",
    )

    hero_description = models.TextField(
        default=(
            "Pomagam odzyskać równowagę między zdrowiem, "
            "samopoczuciem i codziennym stylem życia."
        ),
        verbose_name="Opis Hero",
        help_text=(
            'Aby wyróżnić fragment na stronie, otocz go podwójnymi gwiazdkami. '
            'Przykład: **odŻYWIENIE**.'
        ),
    )

    help_eyebrow = models.CharField(
        max_length=150,
        default="Jak pomagam",
        verbose_name="Mały nagłówek sekcji Jak pomagam",
    )

    help_title = models.CharField(
        max_length=250,
        default="Od poznania Twojej historii do stworzenia planu, który działa",
        verbose_name="Główny nagłówek sekcji Jak pomagam",
    )

    help_description = models.TextField(
        default=(
            "Każdy organizm opowiada własną historię. Chcę się w nią uważnie "
            "wsłuchać, aby lepiej zrozumieć płynące z niego sygnały i wyznaczyć "
            "kierunek działania, który pozwoli odnaleźć klucz do Twojego sukcesu "
            "— niezależnie czy jest nim redukcja wagi, osiągnięcie konkretnych "
            "celów zdrowotnych, poprawa samopoczucia czy realizacja kilku założeń "
            "jednocześnie. W tym celu łączę wiedzę z zakresu dietetyki klinicznej "
            "z elementami fitoterapii, technik oddechowych i aromaterapii."
        ),
        verbose_name="Opis sekcji Jak pomagam",
        help_text=(
            "Aby wyróżnić fragment na stronie, otocz go podwójnymi gwiazdkami. "
            "Przykład: **odŻYWIENIE**."
        ),
    )

    help_specializations_title = models.CharField(
        max_length=250,
        default="Obszary, w których mogę Ci pomóc",
        verbose_name="Nagłówek specjalizacji",
    )

    hero_photo = models.ImageField(
        upload_to="home/hero/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie Hero",
    )

    def __str__(self):
        return "Strona główna"

    class Meta:
        verbose_name = "Strona główna"
        verbose_name_plural = "Strona główna"


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
        help_text=(
            'Aby wyróżnić fragment na stronie, otocz go podwójnymi gwiazdkami. '
            'Przykład: **odŻYWIENIE**.'
        ),
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

    description = models.TextField(
        blank=True,
        verbose_name="Krótki opis",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Wyświetlaj na stronie",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specjalizacja"
        verbose_name_plural = "Specjalizacje"
        ordering = ["order"]


class Service(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Nazwa usługi",
    )

    short_description = models.TextField(
        blank=True,
        verbose_name="Krótki opis",
        help_text="Krótki opis widoczny na karcie oferty.",
    )

    details = models.TextField(
        blank=True,
        verbose_name="Szczegóły usługi",
        help_text="Pełniejszy opis usługi. Wykorzystamy go później na stronie oferty.",
    )

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cena",
        help_text="Pozostaw puste, jeśli cena nie ma być wyświetlana.",
    )

    duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Czas trwania w minutach",
    )

    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie / grafika usługi",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Wyświetlaj na stronie",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Wyróżniona usługa",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Usługa"
        verbose_name_plural = "Usługi"
        ordering = ["order"]      

class CooperationStep(models.Model):
    title = models.CharField(
        max_length=150,
        verbose_name="Nazwa etapu",
        help_text="Tytuł jednego z trzech etapów w sekcji Jak pomagam.",
    )

    description = models.TextField(
        verbose_name="Opis etapu",
        help_text="Opis etapu widoczny pod jego tytułem na stronie głównej.",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Wyświetlaj na stronie",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Etap „Jak pomagam”"
        verbose_name_plural = "Etapy „Jak pomagam”"
        ordering = ["order"]