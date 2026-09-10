from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import TestimonialSubmissionForm
from .models import (
    AboutPage,
    CooperationStep,
    HomePage,
    Service,
    Specialization,
    Testimonial,
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

    testimonials = Testimonial.objects.filter(
        is_active=True,
        consent_confirmed=True,
        status=Testimonial.Status.APPROVED,
    )

    context = {
        "home_page": home_page,
        "about_page": about_page,
        "specializations": specializations,
        "services": services,
        "cooperation_steps": cooperation_steps,
        "testimonials": testimonials,
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


def submit_testimonial(request):
    if request.method == "POST":
        form = TestimonialSubmissionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('submit_testimonial')}?wyslano=1")
    else:
        form = TestimonialSubmissionForm()

    context = {
        "form": form,
        "submitted": request.GET.get("wyslano") == "1",
    }

    return render(
        request,
        "main/submit_testimonial.html",
        context,
    )
