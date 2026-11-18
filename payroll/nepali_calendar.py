"""Bikram Sambat date input and display helpers for payroll."""

import datetime
import re

import nepali_datetime
from django import forms
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady, ValidationError
from django.db.utils import DatabaseError
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
        # The date dimension is the app's persisted mapping. It allows a
        # published month-length correction to take effect without changing
        # records that already store AD dates.
        try:
            from base.models import DateTable

            ad_date = DateTable.objects.filter(bs_date=value.strip()).values_list(
                "ad_date", flat=True
            ).first()
            if ad_date is not None:
                return ad_date
        except (AppRegistryNotReady, DatabaseError):
            pass
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
    try:
        from base.models import DateTable

        bs_value = DateTable.objects.filter(ad_date=value).values_list(
            "bs_date", flat=True
        ).first()
        if bs_value is not None:
            return bs_value
    except (AppRegistryNotReady, DatabaseError):
        # Migrations and pre-dimension installations still use the conversion
        # package until the date table is available.
        pass
    bs_date = nepali_datetime.date.from_datetime_date(value)
    return f"{bs_date.year:04d}-{bs_date.month:02d}-{bs_date.day:02d}"


def nepali_period_bounds(value, period="month"):
    """Return an AD ``(start, end)`` pair for the BS period containing value."""
    if isinstance(value, datetime.datetime):
        value = value.date()
    if not isinstance(value, datetime.date):
        raise TypeError("value must be a date or datetime")
    fields = {
        "year": ("ys", "ye"),
        "fiscal_year": ("fys", "fye"),
        "half_year": ("hs", "he"),
        "quarter": ("qs", "qe"),
        "month": ("ms", "me"),
    }
    if period not in fields:
        raise ValueError(f"Unknown Nepali period: {period}")
    start_field, end_field = fields[period]
    try:
        from base.models import DateTable

        row = DateTable.objects.filter(ad_date=value).values_list(
            start_field, end_field
        ).first()
    except (AppRegistryNotReady, DatabaseError):
        row = None
    if row:
        return row

    bs_date = nepali_datetime.date.from_datetime_date(value)
    start_bs = nepali_datetime.date(bs_date.year, 1, 1)
    if period == "month":
        start_bs = nepali_datetime.date(bs_date.year, bs_date.month, 1)
        month_after = (
            (bs_date.year + 1, 1)
            if bs_date.month == 12
            else (bs_date.year, bs_date.month + 1)
        )
        end_bs = nepali_datetime.date(*month_after, 1) - datetime.timedelta(days=1)
    elif period == "fiscal_year":
        fiscal_year = bs_date.year if bs_date.month >= 4 else bs_date.year - 1
        start_bs = nepali_datetime.date(fiscal_year, 4, 1)
        end_bs = nepali_datetime.date(fiscal_year + 1, 4, 1) - datetime.timedelta(days=1)
    elif period == "half_year":
        fiscal_year = bs_date.year if bs_date.month >= 4 else bs_date.year - 1
        start_month = 4 if 4 <= bs_date.month <= 9 else 10
        start_year = fiscal_year if start_month == 4 else fiscal_year
        if bs_date.month < 4:
            start_month, start_year = 10, fiscal_year
        start_bs = nepali_datetime.date(start_year, start_month, 1)
        end_year, end_month = (start_year, start_month + 6)
        if end_month > 12:
            end_year, end_month = end_year + 1, end_month - 12
        end_bs = nepali_datetime.date(end_year, end_month, 1) - datetime.timedelta(days=1)
    elif period == "quarter":
        fiscal_year = bs_date.year if bs_date.month >= 4 else bs_date.year - 1
        month_index = (bs_date.month - 4) % 12
        start_month = ((month_index // 3) * 3 + 4 - 1) % 12 + 1
        start_year = fiscal_year + (1 if start_month < 4 else 0)
        start_bs = nepali_datetime.date(start_year, start_month, 1)
        end_year, end_month = start_year, start_month + 3
        if end_month > 12:
            end_year, end_month = end_year + 1, end_month - 12
        end_bs = nepali_datetime.date(end_year, end_month, 1) - datetime.timedelta(days=1)
    else:
        start_bs = nepali_datetime.date(bs_date.year, 1, 1)
        end_bs = nepali_datetime.date(bs_date.year + 1, 1, 1) - datetime.timedelta(days=1)
    return start_bs.to_datetime_date(), end_bs.to_datetime_date()


def format_fiscal_year(value):
    """Format the fiscal year containing value as ``2083-084``."""
    start, end = nepali_period_bounds(value, "fiscal_year")
    start_year = int(bikram_sambat_to_display(start).split("-")[0])
    end_year = int(bikram_sambat_to_display(end).split("-")[0])
    return f"{start_year}-{end_year % 100:03d}"


def nepali_month_days(year, month):
    """Return the configured published length of a BS month."""
    try:
        from base.models import NepaliCalendarMonth

        days = NepaliCalendarMonth.objects.filter(
            bs_year=year, bs_month=month
        ).values_list("days_in_month", flat=True).first()
        if days is not None:
            return days
    except (AppRegistryNotReady, DatabaseError):
        pass
    for day in range(32, 28, -1):
        try:
            nepali_datetime.date(year, month, day)
            return day
        except ValueError:
            continue
    raise ValueError(f"No valid month length found for BS {year}-{month:02d}")


def format_payroll_date(value, pad_day=False):
    if isinstance(value, datetime.datetime):
        value = value.date()
    if not isinstance(value, datetime.date):
        return ""
    if nepali_calendar_enabled():
        bs_date = nepali_datetime.date(
            *(int(part) for part in bikram_sambat_to_display(value).split("-"))
        )
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
