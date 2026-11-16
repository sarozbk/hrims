"""Bikram Sambat date input and display helpers for payroll."""

import datetime
import re

import nepali_datetime
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

BS_DATE_PATTERN = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


def nepali_calendar_enabled():
    return getattr(settings, "NEPALI_CALENDAR", False)


def bikram_sambat_to_gregorian(value):
    match = (
        BS_DATE_PATTERN.fullmatch(value.strip()) if isinstance(value, str) else None
    )
    if not match:
        raise ValidationError(
            _("Enter a valid Bikram Sambat date in YYYY-MM-DD format.")
        )
    try:
        bs_date = nepali_datetime.date(*(int(part) for part in match.groups()))
        return bs_date.to_datetime_date()
    except (TypeError, ValueError) as error:
        raise ValidationError(
            _("Enter a valid Bikram Sambat date in YYYY-MM-DD format.")
        ) from error


class BikramSambatDateInput(forms.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if nepali_calendar_enabled():
            context["widget"]["type"] = "text"
            context["widget"]["attrs"].setdefault("placeholder", _("YYYY-MM-DD (BS)"))
            context["widget"]["attrs"].setdefault("autocomplete", "off")
            context["widget"]["attrs"].setdefault("data-nepali-datepicker", "true")
        else:
            context["widget"]["type"] = "date"
            context["widget"]["attrs"].pop("data-nepali-datepicker", None)
        return context

    def format_value(self, value):
        if nepali_calendar_enabled() and isinstance(
            value, (datetime.date, datetime.datetime)
        ):
            return bikram_sambat_to_display(value)
        return super().format_value(value)


def bikram_sambat_to_display(value):
    if isinstance(value, datetime.datetime):
        value = value.date()
    if not isinstance(value, datetime.date):
        return ""
    bs_date = nepali_datetime.date.from_datetime_date(value)
    return f"{bs_date.year:04d}-{bs_date.month:02d}-{bs_date.day:02d}"


def format_payroll_date(value, pad_day=False):
    if isinstance(value, datetime.datetime):
        value = value.date()
    if not isinstance(value, datetime.date):
        return ""
    if nepali_calendar_enabled():
        bs_date = nepali_datetime.date.from_datetime_date(value)
        return f"{bs_date.day} {bs_date.strftime('%B')} {bs_date.year}"
    day = f"{value.day:02}" if pad_day else value.day
    return f"{day} {value:%b %Y}"


class BikramSambatDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        if nepali_calendar_enabled():
            error_messages = dict(kwargs.get("error_messages") or {})
            error_messages.setdefault(
                "invalid",
                _("Enter a valid Bikram Sambat date in YYYY-MM-DD format."),
            )
            kwargs["error_messages"] = error_messages
        kwargs.setdefault("widget", BikramSambatDateInput())
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if nepali_calendar_enabled() and value:
            if isinstance(value, (datetime.date, datetime.datetime)):
                return super().to_python(value)
            if isinstance(value, str) and value.startswith("AD:"):
                return super().to_python(value[3:])
            return bikram_sambat_to_gregorian(value)
        return super().to_python(value)
