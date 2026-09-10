from django.contrib import admin

from .models import (
    AboutPage,
    HomePage,
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
