from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_GET

from .forms import NewsletterSignupForm, TestimonialSubmissionForm
from .models import (
    AboutPage,
    CooperationStep,
    HomePage,
    LegalDocument,
    SiteSettings,
    NEWSLETTER_CONSENT_TEXT,
    NewsletterSubscriber,
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



def newsletter_signup(request):
    if request.method == "POST":
        form = NewsletterSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            subscriber = NewsletterSubscriber.objects.filter(
                email__iexact=email
            ).first()

            if subscriber:
                subscriber.name = form.cleaned_data["name"]
                subscriber.email = email
                subscriber.consent_confirmed = True
                subscriber.consent_text = NEWSLETTER_CONSENT_TEXT
                subscriber.consented_at = timezone.now()
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                subscriber.save(
                    update_fields=[
                        "name",
                        "email",
                        "consent_confirmed",
                        "consent_text",
                        "consented_at",
                        "is_active",
                        "unsubscribed_at",
                    ]
                )
                return redirect(f"{reverse('newsletter_signup')}?zapisano=1")

            try:
                NewsletterSubscriber.objects.create(
                    name=form.cleaned_data["name"],
                    email=email,
                    consent_confirmed=True,
                    consent_text=NEWSLETTER_CONSENT_TEXT,
                )
            except IntegrityError:
                form.add_error(
                    "email",
                    "Ten adres e-mail jest już zapisany do newslettera.",
                )
            else:
                return redirect(f"{reverse('newsletter_signup')}?zapisano=1")
    else:
        form = NewsletterSignupForm()

    return render(
        request,
        "main/newsletter_signup.html",
        {
            "form": form,
            "subscribed": request.GET.get("zapisano") == "1",
        },
    )


def _render_legal_document(request, document_type):
    document = LegalDocument.current(document_type)
    if document is None:
        raise Http404("Dokument nie został jeszcze opublikowany.")

    return render(
        request,
        "main/legal_document.html",
        {
            "document": document,
            "rendered_content": document.rendered_content(
                SiteSettings.objects.first()
            ),
        },
    )


@require_GET
def terms_of_service(request):
    return _render_legal_document(
        request,
        LegalDocument.DocumentType.TERMS,
    )


@require_GET
def privacy_policy(request):
    return _render_legal_document(
        request,
        LegalDocument.DocumentType.PRIVACY,
    )


@require_GET
def cookie_policy(request):
    return _render_legal_document(
        request,
        LegalDocument.DocumentType.COOKIES,
    )
