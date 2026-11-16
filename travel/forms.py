from django import forms

from travel.models import TravelRequest


class TravelRequestForm(forms.ModelForm):
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
            "departure_date": forms.DateInput(attrs={"type": "date"}),
            "return_date": forms.DateInput(attrs={"type": "date"}),
            "purpose": forms.Textarea(attrs={"rows": 3}),
        }
