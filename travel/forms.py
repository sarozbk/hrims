from django import forms
from django.utils.translation import gettext_lazy as _

from payroll.nepali_calendar import BikramSambatDateField
from travel.models import TravelRequest


class TravelRequestForm(forms.ModelForm):
    departure_date = BikramSambatDateField(label=_("Departure Date"))
    return_date = BikramSambatDateField(label=_("Return Date"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "oh-input")

    class Meta:
        model = TravelRequest
        fields = (
            "destination", "purpose", "departure_date", "return_date",
            "mode_of_travel", "estimated_cost",
        )
        widgets = {
            "purpose": forms.Textarea(attrs={"rows": 3}),
        }
