import json
import time
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

# O primeiro modelo vem do .env. Os seguintes servem como fallback caso o
# modelo principal esteja temporariamente indisponível (503/high demand).
FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]


def _processar_resposta(response):
    data = json.loads(response.text)
    if data.get("erro"):
        return None
    data["valor"] = Decimal(str(data["valor"]))
    return data


def _is_unavailable_error(exc):
    texto = str(exc).upper()
    return "503" in texto or "UNAVAILABLE" in texto or "HIGH DEMAND" in texto


def extrair_gasto(mensagem: str = "", audio_bytes: bytes | None = None, audio_mimetype: str = "audio/ogg"):
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = f"{SYSTEM_PROMPT}\ndata_atual={date.today().isoformat()}"

    if audio_bytes:
        mime_type = audio_mimetype.split(";")[0].strip() or "audio/ogg"
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        contents = [prompt, audio_part]
    else:
        contents = f"{prompt}\nmensagem={mensagem}"

    modelos = [settings.GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != settings.GEMINI_MODEL]
    ultimo_erro = None

    for indice, modelo in enumerate(modelos):
        # Faz até 2 tentativas no modelo principal antes de trocar de modelo.
        tentativas = 2 if indice == 0 else 1
        for tentativa in range(tentativas):
            try:
                print(f"Gemini: tentando modelo {modelo} (tentativa {tentativa + 1}/{tentativas})")
                response = client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config={"response_mime_type": "application/json"},
                )
                return _processar_resposta(response)
            except Exception as exc:
                ultimo_erro = exc
                print(f"Gemini: erro no modelo {modelo}: {exc}")
                if not _is_unavailable_error(exc):
                    raise
                if tentativa + 1 < tentativas:
                    time.sleep(2)

        print(f"Gemini: modelo {modelo} indisponível; tentando fallback...")

    raise RuntimeError(f"Gemini indisponível temporariamente. Último erro: {ultimo_erro}")
