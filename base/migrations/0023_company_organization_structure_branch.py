from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("base", "0022_jobposition_headcount")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="organization_structure",
            field=models.CharField(
                choices=[
                    ("single", "One company, one location"),
                    ("branches", "One company with multiple branches"),
                    ("group", "Group with multiple companies"),
                ],
                default="single",
                help_text="Choose how this organization is structured.",
                max_length=20,
                verbose_name="Organization structure",
            ),
        ),
        migrations.CreateModel(
            name="Branch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="Branch name")),
                ("code", models.CharField(blank=True, max_length=30, verbose_name="Branch code")),
                ("address", models.TextField(blank=True, max_length=255, verbose_name="Address")),
                ("country", models.CharField(blank=True, max_length=50, verbose_name="Country")),
                ("state", models.CharField(blank=True, max_length=50, verbose_name="State")),
                ("city", models.CharField(blank=True, max_length=50, verbose_name="City")),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
                (
                    "company_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="branches",
                        to="base.company",
                        verbose_name="Company",
                    ),
                ),
            ],
            options={
                "verbose_name": "Branch",
                "verbose_name_plural": "Branches",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="branch",
            constraint=models.UniqueConstraint(
                fields=("company_id", "name"), name="base_branch_company_name_uniq"
            ),
        ),
        migrations.AddConstraint(
            model_name="branch",
            constraint=models.UniqueConstraint(
                condition=~models.Q(code=""),
                fields=("company_id", "code"),
                name="base_branch_company_code_uniq",
            ),
        ),
    ]
