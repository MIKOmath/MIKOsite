from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "accounts",
            "0010_remove_linkedaccount_accounts_li_externa_ed775c_idx_and_more",
        ),
    ]

    # Temporarily change User.id to a CharField to allow the transition
    # from IntegerField to UUIDField in two steps.
    operations = [
        migrations.AlterField(
            model_name="user",
            name="id",
            field=models.CharField(max_length=36, primary_key=True, serialize=False),
        ),
    ]
