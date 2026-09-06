from django.contrib import admin

from .models import (
    AboutPage,
    HomePage,
    Service,
    SiteSettings,
    Specialization,
    CooperationStep,
)


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
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
        "is_active",
    )

    list_editable = (
        "is_active",
    )

    search_fields = (
        "title",
        "description",
    )

    ordering = (
        "order",
    )


        