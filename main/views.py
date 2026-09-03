from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import (
    AboutPage,
    CooperationStep,
    HomePage,
    Service,
    Specialization,
)


def home(request):
    home_page = HomePage.objects.first()
    about_page = AboutPage.objects.first()

    specializations = Specialization.objects.filter(
        is_active=True
    )

    services = Service.objects.filter(
        is_active=True
    )

    cooperation_steps = CooperationStep.objects.filter(
        is_active=True
    )

    context = {
        "home_page": home_page,
        "about_page": about_page,
        "specializations": specializations,
        "services": services,
        "cooperation_steps": cooperation_steps,
    }

    return render(
        request,
        "main/home.html",
        context,
    )


@require_GET
def calorie_calculator(request):
    # Inputs and calculations stay in the browser; no patient data is stored.
    return render(request, "main/calorie_calculator.html")


def about(request):
    about_page = AboutPage.objects.first()

    specializations = Specialization.objects.filter(
        is_active=True
    )

    context = {
        "about_page": about_page,
        "specializations": specializations,
    }

    return render(
        request,
        "main/about.html",
        context,
    )
