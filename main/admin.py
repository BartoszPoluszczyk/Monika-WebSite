from django.contrib import admin
from django.utils import timezone

from .models import (
    AboutPage,
    HomePage,
    LegalDocument,
    NewsletterSubscriber,
    Service,
    SiteSettings,
    Specialization,
    CooperationStep,
    Testimonial,
)


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
    )

    fieldsets = (
        (
            "Sekcja Hero",
            {
                "fields": (
                    "hero_eyebrow",
                    "hero_title",
                    "hero_description",
                    "hero_photo",
                )
            },
        ),
        (
            "Sekcja Jak pomagam",
            {
                "fields": (
                    "help_eyebrow",
                    "help_title",
                    "help_lead",
                    "help_description",
                    "help_specializations_title",
                )
            },
        ),
        (
            "Sekcja Newsletter",
            {
                "fields": (
                    "newsletter_eyebrow",
                    "newsletter_title",
                    "newsletter_description",
                    "newsletter_button_label",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        if HomePage.objects.exists():
            return False

        return super().has_add_permission(request)


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "name",
        "is_active",
    )

    list_editable = (
        "is_active",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "order",
    )

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Marka",
            {"fields": ("logo", "site_name")},
        ),
        (
            "Dane działalności do dokumentów prawnych",
            {
                "fields": (
                    "owner_name",
                    "business_name",
                    "business_address",
                    "tax_id",
                    "contact_email",
                    "contact_phone",
                ),
                "description": (
                    "Uzupełnij wszystkie pola przed uruchomieniem płatności "
                    "i publicznym udostępnieniem strony."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False

        return super().has_add_permission(request)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "name",
        "price",
        "duration_minutes",
        "is_featured",
        "is_active",
    )

    list_editable = (
        "is_featured",
        "is_active",
    )

    search_fields = (
        "name",
        "short_description",
    )

    ordering = (
        "order",
    )

@admin.register(CooperationStep)
class CooperationStepAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "title",
        "has_image",
        "is_active",
    )

    list_editable = (
        "is_active",
    )

    @admin.display(boolean=True, description="Zdjęcie")
    def has_image(self, obj):
        return bool(obj.image)

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "order",
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "status",
        "rating",
        "consent_confirmed",
        "is_active",
        "order",
        "created_at",
    )

    list_editable = (
        "status",
        "is_active",
        "order",
    )

    list_filter = (
        "status",
        "consent_confirmed",
        "is_active",
    )

    search_fields = (
        "author_name",
        "content",
    )

    ordering = (
        "-created_at",
    )

    actions = (
        "approve_testimonials",
        "reject_testimonials",
    )

    @admin.action(description="Zaakceptuj wybrane opinie")
    def approve_testimonials(self, request, queryset):
        queryset.update(status=Testimonial.Status.APPROVED)

    @admin.action(description="Odrzuć wybrane opinie")
    def reject_testimonials(self, request, queryset):
        queryset.update(status=Testimonial.Status.REJECTED)



@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "name",
        "consent_confirmed",
        "is_active",
        "consented_at",
        "unsubscribed_at",
    )

    list_filter = (
        "consent_confirmed",
        "is_active",
    )

    search_fields = (
        "email",
        "name",
    )

    ordering = (
        "-consented_at",
    )

    readonly_fields = (
        "email",
        "name",
        "consent_confirmed",
        "consent_text",
        "consented_at",
        "unsubscribed_at",
    )

    actions = (
        "deactivate_subscriptions",
    )

    @admin.action(description="Oznacz wybrane zapisy jako wypisane")
    def deactivate_subscriptions(self, request, queryset):
        queryset.filter(is_active=True).update(
            is_active=False,
            unsubscribed_at=timezone.now(),
        )

    def has_add_permission(self, request):
        return False



@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "document_type",
        "version",
        "effective_from",
        "is_published",
        "updated_at",
    )
    list_filter = ("document_type", "is_published")
    search_fields = ("title", "version", "content")
    ordering = ("document_type", "-effective_from", "-pk")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Dokument",
            {
                "fields": (
                    "document_type",
                    "title",
                    "version",
                    "effective_from",
                    "is_published",
                )
            },
        ),
        (
            "Treść",
            {
                "fields": ("content",),
                "description": (
                    "Nie nadpisuj starej wersji zaakceptowanej przez klientów. "
                    "Przy większej zmianie utwórz nowy dokument z nowym numerem wersji."
                ),
            },
        ),
        (
            "Historia",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
