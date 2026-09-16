import json
from datetime import date
from decimal import Decimal

from django.conf import settings
from google import genai


SYSTEM_PROMPT = """
Você é um extrator de gastos financeiros em português do Brasil.
Receba uma mensagem de usuário e responda SOMENTE JSON válido com:
valor (número decimal), descricao (string curta), categoria (uma de: alimentacao, transporte, moradia, saude, lazer, compras, educacao, contas, outros), data (YYYY-MM-DD).
Se não houver uma data explícita, use a data informada no campo data_atual.
Não invente valor. Se não conseguir identificar claramente um gasto, retorne {\"erro\": \"nao_identificado\"}.
"""


def extrair_gasto(mensagem: str):
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = f"{SYSTEM_PROMPT}\ndata_atual={date.today().isoformat()}\nmensagem={mensagem}"
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    data = json.loads(response.text)
    if data.get("erro"):
        return None

    data["valor"] = Decimal(str(data["valor"]))
    return data
