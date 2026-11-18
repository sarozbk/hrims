from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("base", "0024_nepali_date_dimension")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="calendar_system",
            field=models.CharField(
                choices=[
                    ("gregorian", "Gregorian Calendar"),
                    ("nepali", "Nepali Calendar (Bikram Sambat)"),
                ],
                default="nepali",
                help_text="Choose which calendar to use for date selection and display.",
                max_length=12,
                verbose_name="Calendar system",
            ),
        ),
    ]
