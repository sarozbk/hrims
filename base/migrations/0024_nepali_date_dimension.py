from django.db import migrations, models

import base.nepali_calendar_data


def populate_nepali_calendar(apps, schema_editor):
    NepaliCalendarMonth = apps.get_model("base", "NepaliCalendarMonth")
    DateTable = apps.get_model("base", "DateTable")
    base.nepali_calendar_data.seed_calendar_months(NepaliCalendarMonth)
    base.nepali_calendar_data.rebuild_nepali_date_table(
        NepaliCalendarMonth, DateTable
    )


class Migration(migrations.Migration):
    dependencies = [("base", "0023_company_organization_structure_branch")]

    operations = [
        migrations.CreateModel(
            name="DateTable",
            fields=[
                ("ad_date", models.DateField(primary_key=True, serialize=False, verbose_name="AD date")),
                ("bs_date", models.CharField(max_length=10, unique=True, verbose_name="BS date")),
                ("ys", models.DateField(verbose_name="BS year start")),
                ("ye", models.DateField(verbose_name="BS year end")),
                ("fys", models.DateField(verbose_name="Fiscal year start")),
                ("fye", models.DateField(verbose_name="Fiscal year end")),
                ("hs", models.DateField(verbose_name="Half-year start")),
                ("he", models.DateField(verbose_name="Half-year end")),
                ("qs", models.DateField(verbose_name="Quarter start")),
                ("qe", models.DateField(verbose_name="Quarter end")),
                ("ms", models.DateField(verbose_name="BS month start")),
                ("me", models.DateField(verbose_name="BS month end")),
            ],
            options={
                "db_table": "dates_table",
                "ordering": ["ad_date"],
                "verbose_name": "Date table row",
                "verbose_name_plural": "Date table",
            },
        ),
        migrations.CreateModel(
            name="NepaliCalendarMonth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bs_year", models.PositiveSmallIntegerField(verbose_name="BS year")),
                ("bs_month", models.PositiveSmallIntegerField(verbose_name="BS month")),
                ("days_in_month", models.PositiveSmallIntegerField(verbose_name="Days in month")),
            ],
            options={
                "db_table": "nepali_calendar_months",
                "ordering": ["bs_year", "bs_month"],
            },
        ),
        migrations.AddConstraint(
            model_name="nepalicalendarmonth",
            constraint=models.UniqueConstraint(fields=("bs_year", "bs_month"), name="base_nepali_month_uniq"),
        ),
        migrations.AddConstraint(
            model_name="nepalicalendarmonth",
            constraint=models.CheckConstraint(condition=models.Q(("days_in_month__gte", 29), ("days_in_month__lte", 32)), name="base_nepali_month_days_range"),
        ),
        migrations.AddConstraint(
            model_name="nepalicalendarmonth",
            constraint=models.CheckConstraint(condition=models.Q(("bs_month__gte", 1), ("bs_month__lte", 12)), name="base_nepali_month_number_range"),
        ),
        migrations.RunPython(populate_nepali_calendar, migrations.RunPython.noop),
    ]
