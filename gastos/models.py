from django.db import models


class Gasto(models.Model):
    CATEGORIAS = [
        ("alimentacao", "Alimentação"),
        ("transporte", "Transporte"),
        ("moradia", "Moradia"),
        ("saude", "Saúde"),
        ("lazer", "Lazer"),
        ("compras", "Compras"),
        ("educacao", "Educação"),
        ("contas", "Contas"),
        ("outros", "Outros"),
    ]

    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255)
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, default="outros")
    data = models.DateField()
    telefone = models.CharField(max_length=30, blank=True)
    mensagem_original = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]

    def __str__(self):
        return f"R$ {self.valor} - {self.descricao}"
