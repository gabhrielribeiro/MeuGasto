import base64
import json
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

    try:
        payload = json.loads(request.body or "{}")
        mensagem = str(payload.get("message", "")).strip()
        telefone = str(payload.get("phone", "")).strip()
        audio_base64 = payload.get("audio_base64")
        audio_mimetype = str(payload.get("audio_mimetype", "audio/ogg"))

        if not mensagem and not audio_base64:
            return JsonResponse({"erro": "message ou audio_base64 é obrigatório."}, status=400)

        audio_bytes = None
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64, validate=True)
            # Evita receber arquivos de áudio excessivamente grandes no webhook.
            if len(audio_bytes) > 10 * 1024 * 1024:
                return JsonResponse({"ok": False, "resposta": "O áudio é muito grande. Envie uma mensagem de voz menor."}, status=413)

        dados = extrair_gasto(
            mensagem=mensagem,
            audio_bytes=audio_bytes,
            audio_mimetype=audio_mimetype,
        )
        if not dados:
            return JsonResponse({"ok": False, "resposta": "Não consegui identificar um gasto. Exemplo: Gastei 35,90 no mercado."})

        gasto = Gasto.objects.create(
            valor=dados["valor"],
            descricao=dados["descricao"],
            categoria=dados["categoria"],
            data=dados["data"],
            telefone=telefone,
            mensagem_original=mensagem or "[áudio]",
        )
        return JsonResponse({
            "ok": True,
            "gasto_id": gasto.id,
            "resposta": f"Gasto registrado: R$ {gasto.valor:.2f} em {gasto.descricao} ({gasto.get_categoria_display()}).",
        })
    except (ValueError, base64.binascii.Error):
        return JsonResponse({"ok": False, "erro": "Áudio/base64 inválido."}, status=400)
    except Exception as exc:
        return JsonResponse({"ok": False, "erro": str(exc)}, status=500)
