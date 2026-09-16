const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const WEBHOOK_URL = process.env.MEUGASTO_WEBHOOK_URL || 'http://127.0.0.1:8000/api/whatsapp/webhook/';
const client = new Client({ authStrategy: new LocalAuth({ clientId: 'meugasto' }) });

client.on('qr', (qr) => {
  console.log('\nEscaneie o QR Code com o WhatsApp:\n');
  qrcode.generate(qr, { small: true });
});

client.on('ready', () => console.log('WhatsApp conectado ao MeuGasto.'));

client.on('message', async (message) => {
  if (message.fromMe || message.from.endsWith('@g.us')) return;
  try {
    const { data } = await axios.post(WEBHOOK_URL, {
      phone: message.from,
      message: message.body,
    });
    if (data.resposta) await message.reply(data.resposta);
  } catch (error) {
    console.error('Erro no webhook:', error.response?.data || error.message);
    await message.reply('Não consegui registrar seu gasto agora. Tente novamente.');
  }
});

client.initialize();
