from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("employee", "0010_employeeworkinformation_branch"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalemployeeworkinformation",
            name="branch_id",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="base.branch",
                verbose_name="Branch",
            ),
        ),
    ]
