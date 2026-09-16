# MeuGasto

Aplicação Django para registrar gastos por WhatsApp usando IA do Google Gemini e uma ponte de WhatsApp Web para testes, sem depender da API oficial do WhatsApp.

## Arquitetura

- `web/`: aplicação Django e painel financeiro.
- `whatsapp/`: bot Node.js usando WhatsApp Web para testes locais.
- Gemini: interpreta mensagens naturais e transforma em dados estruturados.
- SQLite: banco padrão para desenvolvimento.

## Exemplo

Envie no WhatsApp:

> Gastei 35,90 no mercado hoje

A aplicação tenta identificar valor, descrição, categoria e data e registra o gasto.

## Teste local

### Django

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Configure `GEMINI_API_KEY` no `.env`.

### WhatsApp Web

```bash
cd whatsapp
npm install
npm start
```

Um QR Code será exibido no terminal. Escaneie pelo WhatsApp para conectar uma sessão de teste.

> Esta integração usa automação do WhatsApp Web e é destinada a testes. Não é a API oficial do WhatsApp Business.
