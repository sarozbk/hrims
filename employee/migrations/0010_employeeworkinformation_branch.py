from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0023_company_organization_structure_branch"),
        ("employee", "0009_alter_actiontype_is_active_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="employeeworkinformation",
            name="branch_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="employee_work_information",
                to="base.branch",
                verbose_name="Branch",
            ),
        ),
    ]
