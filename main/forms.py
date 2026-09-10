from django import forms

from .models import Testimonial


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
