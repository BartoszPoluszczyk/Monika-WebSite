from django.contrib import admin

from .models import AboutPage, Specialization


@admin.register(AboutPage)
class AboutPageAdmin(admin.ModelAdmin):
    list_display = ("id", "title")


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)