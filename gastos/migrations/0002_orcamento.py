from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("gastos", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Orcamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("limite_diario", models.DecimalField(decimal_places=2, max_digits=10)),
                ("data_inicio", models.DateField()),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-criado_em"]},
        ),
    ]
