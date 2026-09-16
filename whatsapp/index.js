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
    const payload = {
      phone: message.from,
      message: message.body || '',
    };

    // Mensagens de voz são baixadas pelo WhatsApp Web e enviadas ao Django
    // como base64. O Gemini interpreta o áudio diretamente.
    if (message.hasMedia) {
      const media = await message.downloadMedia();
      if (media && media.mimetype && media.mimetype.startsWith('audio/')) {
        const audioBuffer = Buffer.from(media.data, 'base64');
        if (audioBuffer.length <= 10 * 1024 * 1024) {
          payload.audio_base64 = media.data;
          payload.audio_mimetype = media.mimetype;
        } else {
          await message.reply('O áudio é muito grande. Envie uma mensagem de voz menor.');
          return;
        }
      }
    }

    if (!payload.message && !payload.audio_base64) {
      await message.reply('Envie um gasto por texto ou mensagem de voz. Exemplo: "Gastei 35 reais no mercado."');
      return;
    }

    const { data } = await axios.post(WEBHOOK_URL, payload, {
      maxContentLength: 12 * 1024 * 1024,
      maxBodyLength: 12 * 1024 * 1024,
    });

    if (data.resposta) await message.reply(data.resposta);
  } catch (error) {
    console.error('Erro no webhook:', error.response?.data || error.message);
    await message.reply('Não consegui registrar seu gasto agora. Tente novamente.');
  }
});

client.initialize();
