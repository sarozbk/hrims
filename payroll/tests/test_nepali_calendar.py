from datetime import date

from django.core.exceptions import ValidationError
from django.template import Context, Engine
from django.test import SimpleTestCase, override_settings

from payroll.nepali_calendar import (
    BikramSambatDateField,
    bikram_sambat_to_display,
    format_payroll_date,
)


class BikramSambatDateTests(SimpleTestCase):
    @override_settings(NEPALI_CALENDAR=True)
    def test_field_converts_bikram_sambat_input_to_gregorian_storage(self):
        field = BikramSambatDateField()

        self.assertEqual(field.clean("2083-01-01"), date(2026, 4, 14))
        self.assertIn(
            'value="2083-01-01"', field.widget.render("date", date(2026, 4, 14))
        )
        self.assertIn(
            'data-nepali-datepicker="true"',
            field.widget.render("date", date(2026, 4, 14)),
        )

    @override_settings(NEPALI_CALENDAR=True)
    def test_invalid_bikram_sambat_dates_are_rejected(self):
        with self.assertRaises(ValidationError):
            BikramSambatDateField().clean("2083-13-01")

    @override_settings(NEPALI_CALENDAR=True)
    def test_payroll_date_filter_displays_bikram_sambat(self):
        engine = Engine(
            libraries={
                "payroll_calendar": "payroll.templatetags.payroll_calendar",
            }
        )
        rendered = engine.from_string(
            "{% load payroll_calendar %}{{ day|payroll_date }}"
        ).render(Context({"day": date(2026, 4, 14)}))

        self.assertEqual(rendered, "1 Baishakh 2083")
        self.assertEqual(bikram_sambat_to_display(date(2026, 4, 14)), "2083-01-01")
        self.assertEqual(format_payroll_date(date(2026, 4, 14)), "1 Baishakh 2083")

    @override_settings(NEPALI_CALENDAR=False)
    def test_disabling_the_calendar_keeps_gregorian_form_input(self):
        field = BikramSambatDateField()

        self.assertEqual(field.clean("2026-04-14"), date(2026, 4, 14))
        rendered = field.widget.render("date", date(2026, 4, 14))
        self.assertIn('type="date"', rendered)
        self.assertNotIn("data-nepali-datepicker", rendered)

    @override_settings(NEPALI_CALENDAR=True)
    def test_dashboard_date_links_can_explicitly_keep_gregorian_dates(self):
        self.assertEqual(
            BikramSambatDateField().clean("AD:2026-04-14"), date(2026, 4, 14)
        )
