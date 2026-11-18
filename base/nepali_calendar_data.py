"""Build the database date dimension from the configurable BS month table."""

from datetime import timedelta


def rebuild_nepali_date_table(calendar_month_model=None, date_table_model=None):
    """Rebuild ``dates_table`` using month lengths saved in the database.

    The package's conversion data supplies the initial Gregorian anchor. From
    there, saved month lengths define each following month, so a published
    month-length correction updates both conversion directions consistently.
    Optional model arguments let the initial data migration use historical
    Django models safely.
    """
    if calendar_month_model is None:
        from base.models import DateTable, NepaliCalendarMonth

        calendar_month_model = NepaliCalendarMonth
        date_table_model = DateTable

    import nepali_datetime

    months = list(
        calendar_month_model.objects.order_by("bs_year", "bs_month").values_list(
            "bs_year", "bs_month", "days_in_month"
        )
    )
    if not months:
        return 0

    first_year = months[0][0]
    ad_cursor = nepali_datetime.date(first_year, 1, 1).to_datetime_date()
    starts = {}
    expected_year, expected_month = months[0][0], months[0][1]
    for year, month, days in months:
        if (year, month) != (expected_year, expected_month):
            raise ValueError("Nepali calendar month configuration has a gap")
        starts[(year, month)] = ad_cursor
        ad_cursor += timedelta(days=days)
        expected_year, expected_month = (
            (year + 1, 1) if month == 12 else (year, month + 1)
        )

    def bs_month_start(year, month):
        return starts[(year, month)]

    def next_month(year, month):
        return (year + 1, 1) if month == 12 else (year, month + 1)

    def period_bounds(year, month, grouping_months, offset_month):
        period_index = (month - offset_month) % 12 // grouping_months
        start_month_zero = (offset_month - 1) + period_index * grouping_months
        start_year = year
        if month < offset_month:
            start_year -= 1
        start_year += start_month_zero // 12
        start_month = start_month_zero % 12 + 1
        end_year, end_month = start_year, start_month
        for _ in range(grouping_months):
            end_year, end_month = next_month(end_year, end_month)
        return bs_month_start(start_year, start_month), bs_month_start(
            end_year, end_month
        ) - timedelta(days=1)

    # Fiscal-year boundaries need a complete Shrawan-to-Ashadh span. Start at
    # the first stored Shrawan and stop after the last complete Ashadh.
    first_full_year = next((y for y, m, _ in months if m == 4), None)
    if first_full_year is None:
        return 0
    objects = []
    for year, month, days in months:
        # The dimension holds complete fiscal periods only.
        if (year, month) < (first_full_year, 4):
            continue
        fiscal_year = year if month >= 4 else year - 1
        if (fiscal_year + 1, 4) not in starts:
            continue

        year_start = bs_month_start(year, 1)
        if (year + 1, 1) in starts:
            year_end = bs_month_start(year + 1, 1) - timedelta(days=1)
        else:
            year_end = ad_cursor - timedelta(days=1)

        fiscal_start = bs_month_start(fiscal_year, 4)
        fiscal_end = bs_month_start(fiscal_year + 1, 4) - timedelta(days=1)
        half_start, half_end = period_bounds(year, month, 6, 4)
        quarter_start, quarter_end = period_bounds(year, month, 3, 4)
        next_year, next_month_number = next_month(year, month)
        month_start = bs_month_start(year, month)
        month_end = bs_month_start(next_year, next_month_number) - timedelta(days=1)

        for day_number in range(days):
            ad_date = month_start + timedelta(days=day_number)
            # Month-length corrections can make later derived boundaries shift;
            # the complete FY guard above keeps every stored range valid.
            bs_date = f"{year:04d}-{month:02d}-{day_number + 1:02d}"
            objects.append(
                date_table_model(
                    ad_date=ad_date,
                    bs_date=bs_date,
                    ys=year_start,
                    ye=year_end,
                    fys=fiscal_start,
                    fye=fiscal_end,
                    hs=half_start,
                    he=half_end,
                    qs=quarter_start,
                    qe=quarter_end,
                    ms=month_start,
                    me=month_end,
                )
            )

    # Replace atomically so readers never see a partially rebuilt date table.
    from django.db import transaction

    with transaction.atomic():
        date_table_model.objects.all().delete()
        date_table_model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


def seed_calendar_months(calendar_month_model):
    """Seed editable month lengths from the installed conversion package."""
    import nepali_datetime

    first_year = nepali_datetime.date.min.year
    last_year = nepali_datetime.date.max.year
    objects = []
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            try:
                maximum_day = 32
                nepali_datetime.date(year, month, maximum_day)
            except ValueError:
                maximum_day = 31
                try:
                    nepali_datetime.date(year, month, maximum_day)
                except ValueError:
                    maximum_day = 30
                    try:
                        nepali_datetime.date(year, month, maximum_day)
                    except ValueError:
                        maximum_day = 29
            objects.append(
                calendar_month_model(
                    bs_year=year, bs_month=month, days_in_month=maximum_day
                )
            )
    calendar_month_model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)
