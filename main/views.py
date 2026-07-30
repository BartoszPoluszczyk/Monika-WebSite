from django.shortcuts import render

from .models import AboutPage, Specialization


def home(request):
    return render(request, "main/home.html")


def about(request):
    about_page = AboutPage.objects.first()
    specializations = Specialization.objects.all()

    context = {
        "about_page": about_page,
        "specializations": specializations,
    }

    return render(
        request,
        "main/about.html",
        context,
    )