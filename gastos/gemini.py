import json
from datetime import date
from decimal import Decimal

from django.conf import settings
from google import genai
from google.genai import types


SYSTEM_PROMPT = """
Você é um extrator de gastos financeiros em português do Brasil.
Receba uma mensagem de texto OU um áudio e responda SOMENTE JSON válido com:
valor (número decimal), descricao (string curta), categoria (uma de: alimentacao, transporte, moradia, saude, lazer, compras, educacao, contas, outros), data (YYYY-MM-DD).
Se houver áudio, primeiro entenda o que a pessoa falou e extraia o gasto.
Se não houver uma data explícita, use a data informada no campo data_atual.
Não invente valor. Se não conseguir identificar claramente um gasto, retorne {"erro": "nao_identificado"}.
"""


def _processar_resposta(response):
    data = json.loads(response.text)
    if data.get("erro"):
        return None
    data["valor"] = Decimal(str(data["valor"]))
    return data


def extrair_gasto(mensagem: str = "", audio_bytes: bytes | None = None, audio_mimetype: str = "audio/ogg"):
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = f"{SYSTEM_PROMPT}\ndata_atual={date.today().isoformat()}"

    if audio_bytes:
        # WhatsApp normalmente entrega mensagens de voz como OGG/Opus.
        mime_type = audio_mimetype.split(";")[0].strip() or "audio/ogg"
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        contents = [prompt, audio_part]
    else:
        contents = f"{prompt}\nmensagem={mensagem}"

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config={"response_mime_type": "application/json"},
    )

    return _processar_resposta(response)
