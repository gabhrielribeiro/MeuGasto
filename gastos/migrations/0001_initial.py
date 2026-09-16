from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Gasto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("valor", models.DecimalField(decimal_places=2, max_digits=10)),
                ("descricao", models.CharField(max_length=255)),
                ("categoria", models.CharField(choices=[("alimentacao", "Alimentação"), ("transporte", "Transporte"), ("moradia", "Moradia"), ("saude", "Saúde"), ("lazer", "Lazer"), ("compras", "Compras"), ("educacao", "Educação"), ("contas", "Contas"), ("outros", "Outros")], default="outros", max_length=30)),
                ("data", models.DateField()),
                ("telefone", models.CharField(blank=True, max_length=30)),
                ("mensagem_original", models.TextField(blank=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-data", "-criado_em"]},
        ),
    ]
