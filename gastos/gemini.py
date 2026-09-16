import json
import time
from datetime import date
from decimal import Decimal

from django.conf import settings
from google import genai
from google.genai import types


SYSTEM_PROMPT = """
Você é um extrator de gastos financeiros em português do Brasil.
Receba uma mensagem de texto OU um áudio e responda somente o objeto JSON solicitado.
Extraia valor, descricao, categoria e data.
Categorias permitidas: alimentacao, transporte, moradia, saude, lazer, compras, educacao, contas, outros.
Se não houver data explícita, use data_atual.
Não invente valor. Se não conseguir identificar claramente um gasto, use erro="nao_identificado".
"""

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-2.0-flash-lite",
]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "valor": {"type": "number"},
        "descricao": {"type": "string"},
        "categoria": {
            "type": "string",
            "enum": [
                "alimentacao", "transporte", "moradia", "saude", "lazer",
                "compras", "educacao", "contas", "outros",
            ],
        },
        "data": {"type": "string"},
        "erro": {"type": "string"},
    },
    "required": ["valor", "descricao", "categoria", "data"],
}


def _processar_resposta(response):
    parsed = getattr(response, "parsed", None)
    if parsed:
        if hasattr(parsed, "model_dump"):
            data = parsed.model_dump()
        elif isinstance(parsed, dict):
            data = parsed
        else:
            data = None
        if data:
            if data.get("erro"):
                return None
            data["valor"] = Decimal(str(data["valor"]))
            return data

    texto = (getattr(response, "text", None) or "").strip()
    if not texto:
        raise RuntimeError("Gemini retornou resposta vazia.")

    if texto.startswith("```"):
        texto = texto.replace("```json", "", 1).replace("```", "").strip()

    try:
        data = json.loads(texto)
    except json.JSONDecodeError:
        inicio = texto.find("{")
        fim = texto.rfind("}")
        if inicio < 0 or fim <= inicio:
            raise
        data = json.loads(texto[inicio:fim + 1])

    if data.get("erro"):
        return None
    data["valor"] = Decimal(str(data["valor"]))
    return data


def _is_retryable_error(exc):
    texto = str(exc).upper()
    return (
        "503" in texto
        or "UNAVAILABLE" in texto
        or "HIGH DEMAND" in texto
        or "RESPOSTA VAZIA" in texto
        or "EXPECTING VALUE" in texto
        or "JSONDECODEERROR" in texto
        or "UNTERMINATED STRING" in texto
        or "429" in texto
        or "RESOURCE_EXHAUSTED" in texto
    )


def _is_model_not_found_error(exc):
    texto = str(exc).upper()
    return "404" in texto or "NOT_FOUND" in texto or "NO LONGER AVAILABLE" in texto


def _log_diagnostico(response):
    try:
        candidatos = getattr(response, "candidates", None) or []
        if candidatos:
            candidato = candidatos[0]
            print("Gemini finish_reason:", getattr(candidato, "finish_reason", None))
            print("Gemini safety_ratings:", getattr(candidato, "safety_ratings", None))
    except Exception:
        pass


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
        # O modelo principal recebe uma segunda tentativa; erros de JSON também
        # acionam o fallback para evitar devolver 400 ao WhatsApp.
        tentativas = 2 if indice == 0 else 1
        for tentativa in range(tentativas):
            try:
                print(f"Gemini: {modelo} ({tentativa + 1}/{tentativas})")
                response = client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": RESPONSE_SCHEMA,
                        "temperature": 0,
                        "max_output_tokens": 256,
                    },
                )
                try:
                    return _processar_resposta(response)
                except (RuntimeError, json.JSONDecodeError):
                    _log_diagnostico(response)
                    raise
            except Exception as exc:
                ultimo_erro = exc
                print(f"Gemini: erro: {exc}")

                if _is_model_not_found_error(exc):
                    break

                if _is_retryable_error(exc):
                    if tentativa + 1 < tentativas:
                        time.sleep(1)
                    continue

                raise

    raise RuntimeError(f"Gemini indisponível temporariamente. Último erro: {ultimo_erro}")
