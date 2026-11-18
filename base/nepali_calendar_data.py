"""Build the database date dimension from the configurable BS month table."""

from datetime import timedelta


def rebuild_nepali_date_table(calendar_month_model=None, date_table_model=None):
    """Rebuild ``dates_table`` from year-anchored, configurable BS month data.

    The first day of each BS year is anchored to the conversion package's
    published AD mapping. Month lengths then define the dates within that year.
    They must add up exactly to the next year's anchor, which prevents a
    correction in one year from shifting every later year.
    """
    if calendar_month_model is None:
        from base.models import DateTable, NepaliCalendarMonth

        calendar_month_model = NepaliCalendarMonth
        date_table_model = DateTable

    import nepali_datetime

    try:
        from horilla.week import first_day_of_week

        week_day = first_day_of_week()
    except Exception:
        week_day = 1

    rows = list(
        calendar_month_model.objects.order_by("bs_year", "bs_month").values_list(
            "bs_year", "bs_month", "days_in_month", "bs_year_start_ad"
        )
    )
    if not rows:
        return 0

    months = {(year, month): days for year, month, days, _anchor in rows}
    anchors = {}
    for year in sorted({row[0] for row in rows}):
        configured_anchor = next(
            (anchor for y, m, _days, anchor in rows if y == year and m == 1), None
        )
        anchors[year] = configured_anchor or nepali_datetime.date(
            year, 1, 1
        ).to_datetime_date()

    starts = {}
    ends = {}
    years = sorted(anchors)
    for index, year in enumerate(years):
        if not all((year, month) in months for month in range(1, 13)):
            raise ValueError(f"BS {year} must have all 12 configured months")
        cursor = anchors[year]
        for month in range(1, 13):
            starts[(year, month)] = cursor
            cursor += timedelta(days=months[(year, month)])
            ends[(year, month)] = cursor - timedelta(days=1)
        if index + 1 < len(years):
            next_year = years[index + 1]
            if next_year != year + 1:
                raise ValueError("Nepali calendar year configuration has a gap")
            if cursor != anchors[next_year]:
                raise ValueError(
                    f"BS {year} month lengths end on {cursor - timedelta(days=1)}, "
                    f"but BS {next_year} begins on {anchors[next_year]}; "
                    "correct the published month lengths before rebuilding."
                )

    def next_month(year, month):
        return (year + 1, 1) if month == 12 else (year, month + 1)

    def grouped_period(year, month, size):
        # Fiscal periods begin in BS month 4 (Shrawan).
        index = (month - 4) % 12
        start_month = ((index // size) * size + 3) % 12 + 1
        start_year = year
        # A fiscal half that contains months 1-3 began in month 10 of the
        # previous BS year; the third quarter begins in month 1 of this year.
        if month < 4 and start_month >= 4:
            start_year = year - 1
        elif month >= 4 and start_month < 4:
            start_year = year + 1
        end_year, end_month = start_year, start_month
        for _ in range(size):
            end_year, end_month = next_month(end_year, end_month)
        if (start_year, start_month) not in starts or (end_year, end_month) not in starts:
            return None
        return starts[(start_year, start_month)], starts[(end_year, end_month)] - timedelta(days=1)

    # Keep only dates whose complete FY boundaries are available in the table.
    first_full_year = next((year for year in years if (year, 4) in starts), None)
    objects = []
    for year in years:
        for month in range(1, 13):
            fiscal_year = year if month >= 4 else year - 1
            if (
                first_full_year is None
                or (year, month) < (first_full_year, 4)
                or (fiscal_year, 4) not in starts
                or (fiscal_year + 1, 4) not in starts
            ):
                continue
            fiscal_start = starts[(fiscal_year, 4)]
            fiscal_end = starts[(fiscal_year + 1, 4)] - timedelta(days=1)
            half = grouped_period(year, month, 6)
            quarter = grouped_period(year, month, 3)
            if half is None or quarter is None:
                continue
            month_start, month_end = starts[(year, month)], ends[(year, month)]
            for day_number in range(months[(year, month)]):
                ad_date = month_start + timedelta(days=day_number)
                # Python weekday is Monday=0; this app setting uses Sunday=0.
                weekday = (ad_date.weekday() + 1) % 7
                week_start = ad_date - timedelta(days=(weekday - week_day) % 7)
                objects.append(
                    date_table_model(
                        ad_date=ad_date,
                        bs_date=f"{year:04d}-{month:02d}-{day_number + 1:02d}",
                        ys=anchors[year],
                        ye=ends[(year, 12)],
                        fys=fiscal_start,
                        fye=fiscal_end,
                        ws=week_start,
                        we=week_start + timedelta(days=6),
                        hs=half[0],
                        he=half[1],
                        qs=quarter[0],
                        qe=quarter[1],
                        ms=month_start,
                        me=month_end,
                    )
                )

    from django.db import transaction

    with transaction.atomic():
        date_table_model.objects.all().delete()
        date_table_model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


def seed_calendar_months(calendar_month_model):
    """Seed editable month lengths and BS new-year anchors from the package."""
    import nepali_datetime

    first_year = nepali_datetime.date.min.year
    last_year = nepali_datetime.date.max.year
    objects = []
    for year in range(first_year, last_year + 1):
        for month in range(1, 13):
            maximum_day = next(
                day
                for day in range(32, 28, -1)
                if _valid_bs_day(nepali_datetime, year, month, day)
            )
            objects.append(
                calendar_month_model(
                    bs_year=year,
                    bs_month=month,
                    days_in_month=maximum_day,
                    bs_year_start_ad=(
                        nepali_datetime.date(year, 1, 1).to_datetime_date()
                        if month == 1
                        else None
                    ),
                )
            )
    calendar_month_model.objects.bulk_create(objects, batch_size=1000)
    return len(objects)


def _valid_bs_day(nepali_datetime, year, month, day):
    try:
        nepali_datetime.date(year, month, day)
        return True
    except ValueError:
        return False
