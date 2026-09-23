from django import forms

from .models import Appointment


class AppointmentBookingForm(forms.ModelForm):
    consent_privacy = forms.BooleanField(
        required=True,
        label="Potwierdzam, że zapoznałem się z Polityką prywatności.",
    )
    terms_accepted = forms.BooleanField(
        required=True,
        label="Akceptuję Regulamin świadczenia usług.",
    )
    appointment_date = forms.DateField(widget=forms.HiddenInput())
    appointment_time = forms.ChoiceField(
        label="Godzina wizyty",
        choices=(),
        widget=forms.RadioSelect(),
    )

    class Meta:
        model = Appointment
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "visit_type",
            "notes",
            "consent_privacy",
            "terms_accepted",
        ]
        labels = {
            "notes": "Wiadomość (opcjonalnie)",
            "consent_privacy": "Potwierdzam, że zapoznałem się z Polityką prywatności.",
            "terms_accepted": "Akceptuję Regulamin świadczenia usług.",
        }
        help_texts = {
            "notes": "Nie podawaj tutaj szczegółowych informacji o stanie zdrowia.",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "Imię"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name", "placeholder": "Nazwisko"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "adres@email.pl"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+48 000 000 000"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Krótka informacja organizacyjna"}),
        }

    def __init__(self, *args, available_slots=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["appointment_time"].choices = [
            (slot.strftime("%H:%M"), slot.strftime("%H:%M"))
            for slot in (available_slots or [])
        ]


class AppointmentRescheduleForm(forms.Form):
    appointment_date = forms.DateField(widget=forms.HiddenInput())
    appointment_time = forms.ChoiceField(
        label="Nowa godzina wizyty",
        choices=(),
        widget=forms.RadioSelect(),
    )

    def __init__(self, *args, available_slots=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["appointment_time"].choices = [
            (slot.strftime("%H:%M"), slot.strftime("%H:%M"))
            for slot in (available_slots or [])
        ]
