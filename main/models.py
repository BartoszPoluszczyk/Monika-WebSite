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

    owner_name = models.CharField(
        max_length=180,
        default="Monika Kulik",
        verbose_name="Imię i nazwisko właścicielki",
    )

    business_name = models.CharField(
        max_length=220,
        blank=True,
        verbose_name="Pełna nazwa działalności",
        help_text="Nazwa używana w regulaminie i polityce prywatności.",
    )

    business_address = models.TextField(
        blank=True,
        verbose_name="Adres działalności",
    )

    tax_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="NIP",
    )

    contact_email = models.EmailField(
        blank=True,
        verbose_name="E-mail kontaktowy",
    )

    contact_phone = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Telefon kontaktowy",
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
        default="Indywidualne podejście",
        verbose_name="Nadtytuł sekcji Jak pomagam",
    )

    help_title = models.CharField(
        max_length=250,
        default="Jak pomagam?",
        verbose_name="Główny nagłówek sekcji Jak pomagam",
    )

    help_lead = models.CharField(
        max_length=250,
        default="Od poznania Twojej historii do stworzenia planu, który działa",
        verbose_name="Krótki wstęp sekcji Jak pomagam",
        help_text="Tekst widoczny pod dużym nagłówkiem po lewej stronie sekcji.",
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

    newsletter_eyebrow = models.CharField(
        max_length=100,
        default="Newsletter",
        verbose_name="Nadtytuł sekcji Newsletter",
    )

    newsletter_title = models.CharField(
        max_length=250,
        default="Zdrowa wiedza prosto na Twoją skrzynkę",
        verbose_name="Nagłówek sekcji Newsletter",
    )

    newsletter_description = models.TextField(
        default=(
            "Zapisz się, aby otrzymywać praktyczne wskazówki żywieniowe, "
            "inspiracje i informacje o nowych materiałach."
        ),
        verbose_name="Opis sekcji Newsletter",
    )

    newsletter_button_label = models.CharField(
        max_length=100,
        default="Zapisz się na newsletter",
        verbose_name="Tekst przycisku Newsletter",
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

    image = models.ImageField(
        upload_to="help_steps/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie etapu",
        help_text="Poziome zdjęcie po prawej stronie etapu. Najlepiej w proporcji około 2:1.",
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


class Testimonial(models.Model):
    RATING_CHOICES = [(value, str(value)) for value in range(1, 6)]

    class Status(models.TextChoices):
        PENDING = "pending", "Oczekuje na moderację"
        APPROVED = "approved", "Zaakceptowana"
        REJECTED = "rejected", "Odrzucona"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status moderacji",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data zgłoszenia",
    )

    author_name = models.CharField(
        max_length=150,
        verbose_name="Imię pacjenta / inicjały",
        help_text="Np. „Anna K.” — dokładnie tak, jak pacjent zgodził się to opublikować.",
    )

    content = models.TextField(
        verbose_name="Treść opinii",
    )

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        blank=True,
        null=True,
        verbose_name="Ocena (1-5)",
    )

    photo = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        null=True,
        verbose_name="Zdjęcie pacjenta",
    )

    consent_confirmed = models.BooleanField(
        default=False,
        verbose_name="Pacjent wyraził zgodę na publikację",
        help_text="Zaznacz dopiero po uzyskaniu wyraźnej zgody pacjenta. Opinia nie pojawi się na stronie bez tego.",
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Kolejność",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Wyświetlaj na stronie",
    )

    @property
    def full_stars(self):
        return range(self.rating or 0)

    @property
    def empty_stars(self):
        return range(5 - (self.rating or 0))

    def __str__(self):
        return self.author_name

    class Meta:
        verbose_name = "Opinia pacjenta"
        verbose_name_plural = "Opinie pacjentów"
        ordering = ["order"]

NEWSLETTER_CONSENT_TEXT = (
    "Wyrażam zgodę na przetwarzanie moich danych osobowych (imienia i adresu "
    "e-mail) w celu wysyłki newslettera zawierającego treści informacyjne "
    "i handlowe (marketing)."
)


class NewsletterSubscriber(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name="Imię",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Adres e-mail",
    )

    consent_confirmed = models.BooleanField(
        default=False,
        verbose_name="Zgoda marketingowa",
    )

    consent_text = models.TextField(
        verbose_name="Treść udzielonej zgody",
        help_text="Treść zgody zapisana w chwili zapisu do newslettera.",
    )

    consented_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data udzielenia zgody",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktywny zapis",
    )

    unsubscribed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data rezygnacji",
    )

    def __str__(self):
        return f"{self.name} <{self.email}>"

    class Meta:
        verbose_name = "Zapis do newslettera"
        verbose_name_plural = "Zapisy do newslettera"
        ordering = ["-consented_at"]



class LegalDocument(models.Model):
    class DocumentType(models.TextChoices):
        TERMS = "terms", "Regulamin świadczenia usług"
        PRIVACY = "privacy", "Polityka prywatności"
        COOKIES = "cookies", "Polityka plików cookies"

    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        verbose_name="Rodzaj dokumentu",
    )
    title = models.CharField(max_length=200, verbose_name="Tytuł")
    version = models.CharField(
        max_length=30,
        verbose_name="Wersja",
        help_text="Np. 1.0 albo 2026-09-23.",
    )
    effective_from = models.DateField(verbose_name="Obowiązuje od")
    content = models.TextField(
        verbose_name="Treść dokumentu",
        help_text=(
            "Możesz użyć znaczników: {{BUSINESS_NAME}}, {{OWNER_NAME}}, "
            "{{ADDRESS}}, {{TAX_ID}}, {{EMAIL}}, {{PHONE}}."
        ),
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Opublikowany",
        help_text="Tylko opublikowane dokumenty są widoczne na stronie.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    @classmethod
    def current(cls, document_type, on_date=None):
        from django.utils import timezone

        on_date = on_date or timezone.localdate()
        return (
            cls.objects.filter(
                document_type=document_type,
                is_published=True,
                effective_from__lte=on_date,
            )
            .order_by("-effective_from", "-pk")
            .first()
        )

    def rendered_content(self, site_settings=None):
        site_settings = site_settings or SiteSettings.objects.first()
        owner_name = (
            site_settings.owner_name
            if site_settings and site_settings.owner_name
            else "Monika Kulik"
        )
        business_name = (
            site_settings.business_name
            if site_settings and site_settings.business_name
            else owner_name
        )
        replacements = {
            "{{BUSINESS_NAME}}": business_name,
            "{{OWNER_NAME}}": owner_name,
            "{{ADDRESS}}": (
                site_settings.business_address
                if site_settings and site_settings.business_address
                else "[uzupełnij adres w panelu administratora]"
            ),
            "{{TAX_ID}}": (
                site_settings.tax_id
                if site_settings and site_settings.tax_id
                else "[uzupełnij NIP w panelu administratora]"
            ),
            "{{EMAIL}}": (
                site_settings.contact_email
                if site_settings and site_settings.contact_email
                else "[uzupełnij e-mail w panelu administratora]"
            ),
            "{{PHONE}}": (
                site_settings.contact_phone
                if site_settings and site_settings.contact_phone
                else "[uzupełnij telefon w panelu administratora]"
            ),
        }
        rendered = self.content
        for marker, value in replacements.items():
            rendered = rendered.replace(marker, value)
        return rendered

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.version}"

    class Meta:
        verbose_name = "Dokument prawny"
        verbose_name_plural = "Dokumenty prawne"
        ordering = ["document_type", "-effective_from", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_type", "version"],
                name="unique_legal_document_version",
            ),
        ]
