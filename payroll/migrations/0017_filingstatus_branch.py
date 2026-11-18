import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0023_company_organization_structure_branch"),
        ("payroll", "0016_alter_payrollbatch_status_payadjustment"),
    ]

    operations = [
        migrations.AddField(
            model_name="filingstatus",
            name="branch_id",
            field=models.ForeignKey(
                blank=True,
                help_text="Leave blank to share these tax rules across all branches.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="filing_statuses",
                to="base.branch",
                verbose_name="Branch",
            ),
        ),
    ]
