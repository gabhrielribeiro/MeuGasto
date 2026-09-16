from django.contrib import admin
from .models import Gasto


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ("valor", "descricao", "categoria", "data", "telefone", "criado_em")
    list_filter = ("categoria", "data")
    search_fields = ("descricao", "telefone", "mensagem_original")
