# Ponte WhatsApp Web

Esta pasta contém uma ponte de testes baseada em WhatsApp Web. Ela recebe mensagens de uma sessão do WhatsApp Web, envia o texto ao webhook Django e responde ao usuário com o resultado.

## Uso

1. Tenha Node.js instalado.
2. Entre nesta pasta e rode `npm install`.
3. Inicie com `npm start`.
4. Escaneie o QR Code mostrado no terminal.
5. Mantenha o Django rodando em `http://127.0.0.1:8000`.
6. Envie uma mensagem privada para a conta conectada, por exemplo: `Gastei 42 reais no mercado`.

A URL pode ser alterada com `MEUGASTO_WEBHOOK_URL`.

**Importante:** é uma integração de automação via WhatsApp Web para protótipo/testes, não a API oficial do WhatsApp Business.
