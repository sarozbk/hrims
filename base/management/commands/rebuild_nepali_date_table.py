"""Rebuild the Nepali calendar lookup rows after published month corrections."""

from django.core.management.base import BaseCommand

from base.nepali_calendar_data import rebuild_nepali_date_table


class Command(BaseCommand):
    help = "Rebuild dates_table from the configured Bikram Sambat month lengths."

    def handle(self, *args, **options):
        count = rebuild_nepali_date_table()
        self.stdout.write(self.style.SUCCESS(f"Rebuilt {count:,} Nepali date rows."))
