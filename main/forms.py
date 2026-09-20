from django import forms

from .models import NEWSLETTER_CONSENT_TEXT, NewsletterSubscriber, Testimonial


class TestimonialSubmissionForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["author_name", "content", "rating", "consent_confirmed"]
        labels = {
            "author_name": "Imię lub inicjały",
            "content": "Twoja opinia",
            "rating": "Ocena (opcjonalnie)",
            "consent_confirmed": (
                "Wyrażam zgodę na publikację mojej opinii (wraz z podanym imieniem) na stronie."
            ),
        }
        widgets = {
            "author_name": forms.TextInput(attrs={"placeholder": "Np. Anna K.", "autocomplete": "name"}),
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": "Opisz swoje doświadczenie ze współpracy"}),
            "rating": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # BooleanField form fields default to required=False (an unchecked checkbox
        # submits nothing), but publishing without consent must not be possible.
        self.fields["consent_confirmed"].required = True



class NewsletterSignupForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label="Imię",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Podaj swoje imię",
                "autocomplete": "given-name",
            }
        ),
    )
    email = forms.EmailField(
        label="Adres e-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Podaj swój adres e-mail",
                "autocomplete": "email",
            }
        ),
    )
    consent = forms.BooleanField(
        required=True,
        label=NEWSLETTER_CONSENT_TEXT,
        error_messages={
            "required": "Zaznacz zgodę, aby zapisać się do newslettera.",
        },
    )
    website = forms.CharField(
        required=False,
        label="Pozostaw to pole puste",
        widget=forms.HiddenInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
            }
        ),
    )

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if NewsletterSubscriber.objects.filter(
            email__iexact=email,
            is_active=True,
        ).exists():
            raise forms.ValidationError("Ten adres e-mail jest już zapisany do newslettera.")
        return email

    def clean_website(self):
        value = self.cleaned_data["website"]
        if value:
            raise forms.ValidationError("Nie udało się wysłać formularza.")
        return value
