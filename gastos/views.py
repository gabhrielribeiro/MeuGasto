from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .gemini import extrair_gasto
from .models import Gasto


def dashboard(request):
    gastos = Gasto.objects.all()[:50]
    total = Gasto.objects.aggregate(total=Sum("valor"))["total"] or Decimal("0")
    hoje = Gasto.objects.filter(data=date.today()).aggregate(total=Sum("valor"))["total"] or Decimal("0")
    return render(request, "gastos/dashboard.html", {"gastos": gastos, "total": total, "hoje": hoje})


@csrf_exempt
def whatsapp_webhook(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Use POST."}, status=405)

    import json
    try:
        payload = json.loads(request.body or "{}")
        mensagem = str(payload.get("message", "")).strip()
        telefone = str(payload.get("phone", "")).strip()
        if not mensagem:
            return JsonResponse({"erro": "message é obrigatório."}, status=400)

        dados = extrair_gasto(mensagem)
        if not dados:
            return JsonResponse({"ok": False, "resposta": "Não consegui identificar um gasto. Exemplo: Gastei 35,90 no mercado."})

        gasto = Gasto.objects.create(
            valor=dados["valor"],
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            data=dados["data"],
            telefone=telefone,
            mensagem_original=mensagem,
        )
        return JsonResponse({
            "ok": True,
            "gasto_id": gasto.id,
            "resposta": f"Gasto registrado: R$ {gasto.valor:.2f} em {gasto.descricao} ({gasto.get_categoria_display()}).",
        })
    except Exception as exc:
        return JsonResponse({"ok": False, "erro": str(exc)}, status=500)
