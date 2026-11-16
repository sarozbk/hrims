from django import template
from django.template.defaultfilters import date as django_date

from payroll.nepali_calendar import (
    BikramSambatDateInput,
    format_payroll_date,
    nepali_calendar_enabled,
)

register = template.Library()


@register.filter
def payroll_date(value, date_format="j M Y"):
    if not value:
        return ""
    if nepali_calendar_enabled():
        return format_payroll_date(value)
    return django_date(value, date_format)


@register.simple_tag
def nepali_calendar_is_enabled():
    return nepali_calendar_enabled()


@register.filter
def has_nepali_date_input(form):
    return nepali_calendar_enabled() and any(
        isinstance(field.widget, BikramSambatDateInput)
        and field.widget.attrs.get("data-nepali-datepicker") != "false"
        for field in form.fields.values()
    )
