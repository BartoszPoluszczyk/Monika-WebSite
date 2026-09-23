from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import (
    AboutPage,
    HomePage,
    LegalDocument,
    NewsletterCampaign,
    NewsletterDelivery,
    NewsletterSubscriber,
    Service,
    SiteSettings,
    Specialization,
    CooperationStep,
    Testimonial,
)

from .newsletter import (
    build_campaign_context,
    send_campaign,
    send_test_campaign,
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
        "confirmed_at",
        "is_active",
        "consented_at",
        "unsubscribed_at",
    )

    list_filter = (
        "consent_confirmed",
        "is_active",
        "confirmed_at",
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
        "confirmation_sent_at",
        "confirmed_at",
        "unsubscribed_at",
    )

    actions = (
        "deactivate_subscriptions",
    )

    @admin.action(description="Oznacz wybrane zapisy jako wypisane")
    def deactivate_subscriptions(self, request, queryset):
        updated = queryset.filter(is_active=True).update(
            is_active=False,
            unsubscribed_at=timezone.now(),
        )
        self.message_user(
            request,
            f"Wypisano: {updated}.",
            messages.SUCCESS,
        )

    def has_add_permission(self, request):
        return False


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "status",
        "scheduled_at",
        "sent_at",
        "recipient_count",
        "failed_count",
    )
    list_filter = ("status", "scheduled_at", "sent_at")
    search_fields = ("title", "subject", "heading", "content")
    ordering = ("-created_at",)
    actions = ("send_test_messages", "send_selected_campaigns")
    readonly_fields = (
        "preview_link",
        "sent_at",
        "recipient_count",
        "failed_count",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Treść wiadomości",
            {
                "fields": (
                    "title",
                    "subject",
                    "preheader",
                    "heading",
                    "content",
                    "image",
                    "button_label",
                    "button_url",
                )
            },
        ),
        (
            "Podgląd i wysyłka testowa",
            {
                "fields": ("preview_link", "test_recipient_email"),
                "description": (
                    "Zapisz kampanię, otwórz podgląd, a następnie użyj akcji "
                    "„Wyślij test wybranych kampanii”."
                ),
            },
        ),
        (
            "Publikacja",
            {
                "fields": ("status", "scheduled_at"),
                "description": (
                    "Do właściwej wysyłki wymagany jest status "
                    "„Gotowa do wysyłki”."
                ),
            },
        ),
        (
            "Wyniki",
            {
                "fields": (
                    "sent_at",
                    "recipient_count",
                    "failed_count",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/preview/",
                self.admin_site.admin_view(self.preview_view),
                name="main_newslettercampaign_preview",
            )
        ]
        return custom_urls + super().get_urls()

    def preview_view(self, request, object_id):
        campaign = get_object_or_404(NewsletterCampaign, pk=object_id)
        return render(
            request,
            "main/emails/newsletter_campaign.html",
            build_campaign_context(campaign),
        )

    @admin.display(description="Podgląd wiadomości")
    def preview_link(self, obj):
        if not obj or not obj.pk:
            return "Zapisz kampanię, aby zobaczyć podgląd."
        url = reverse(
            "admin:main_newslettercampaign_preview",
            args=[obj.pk],
        )
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Otwórz podgląd</a>',
            url,
        )

    @admin.action(description="Wyślij test wybranych kampanii")
    def send_test_messages(self, request, queryset):
        sent = 0
        for campaign in queryset:
            recipient = campaign.test_recipient_email or request.user.email
            if not recipient:
                self.message_user(
                    request,
                    (
                        f"„{campaign.title}”: uzupełnij adres do wysyłki "
                        "testowej albo e-mail konta administratora."
                    ),
                    messages.ERROR,
                )
                continue
            try:
                send_test_campaign(campaign, recipient)
            except Exception as error:
                self.message_user(
                    request,
                    f"„{campaign.title}”: błąd testu — {error}",
                    messages.ERROR,
                )
            else:
                sent += 1
        if sent:
            self.message_user(
                request,
                f"Wysłano wiadomości testowe: {sent}.",
                messages.SUCCESS,
            )

    @admin.action(description="Wyślij wybrane kampanie teraz")
    def send_selected_campaigns(self, request, queryset):
        for campaign in queryset:
            try:
                sent_count, failed_count = send_campaign(
                    campaign.pk,
                    force=True,
                )
            except (ValueError, NewsletterCampaign.DoesNotExist) as error:
                self.message_user(
                    request,
                    f"„{campaign.title}”: {error}",
                    messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    (
                        f"„{campaign.title}”: wysłano {sent_count}, "
                        f"błędy {failed_count}."
                    ),
                    (
                        messages.WARNING
                        if failed_count
                        else messages.SUCCESS
                    ),
                )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == NewsletterCampaign.Status.SENT:
            fields.extend(
                [
                    "title",
                    "subject",
                    "preheader",
                    "heading",
                    "content",
                    "image",
                    "button_label",
                    "button_url",
                    "test_recipient_email",
                    "status",
                    "scheduled_at",
                ]
            )
        return tuple(dict.fromkeys(fields))

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == NewsletterCampaign.Status.SENT:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(NewsletterDelivery)
class NewsletterDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "subscriber_email",
        "status",
        "sent_at",
        "created_at",
    )
    list_filter = ("status", "campaign")
    search_fields = (
        "subscriber_email",
        "campaign__title",
        "error_message",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "campaign",
        "subscriber",
        "subscriber_email",
        "status",
        "sent_at",
        "error_message",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method in {"GET", "HEAD", "OPTIONS"}

    def has_delete_permission(self, request, obj=None):
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
