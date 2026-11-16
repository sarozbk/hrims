# Generated for the initial travel request model.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("employee", "0009_alter_actiontype_is_active_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TravelRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Created At")),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                ("destination", models.CharField(max_length=255, verbose_name="Destination")),
                ("purpose", models.TextField(verbose_name="Purpose of Travel")),
                ("departure_date", models.DateField(verbose_name="Departure Date")),
                ("return_date", models.DateField(verbose_name="Return Date")),
                ("mode_of_travel", models.CharField(blank=True, max_length=100, verbose_name="Mode of Travel")),
                ("estimated_cost", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Estimated Cost")),
                ("status", models.CharField(choices=[("requested", "Requested"), ("approved", "Approved"), ("rejected", "Rejected")], default="requested", max_length=20)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("reject_reason", models.TextField(blank=True, verbose_name="Rejection Reason")),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_travel_requests", to="employee.employee", verbose_name="Approved By")),
                ("created_by", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="travel_requests", to="employee.employee", verbose_name="Employee")),
                ("modified_by", models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_modified_by", to=settings.AUTH_USER_MODEL, verbose_name="Modified By")),
            ],
            options={
                "verbose_name": "Travel Request",
                "verbose_name_plural": "Travel Requests",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
