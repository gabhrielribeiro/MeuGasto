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

    if (message.hasMedia) {
      console.log('Mídia recebida. Preparando áudio...');

      // O WhatsApp Web passou a expor o ID serializado em "$1" em algumas
      // versões. whatsapp-web.js ainda consulta "_serialized" em downloadMedia().
      // Recriamos o valor esperado antes de chamar a biblioteca.
      if (message.id && !message.id._serialized && message.id.$1) {
        message.id._serialized = message.id.$1;
      }

      if (message.id && !message.id._serialized && message.id.remote && message.id.id) {
        message.id._serialized = `${message.id.fromMe}_${message.id.remote}_${message.id.id}`;
      }

      console.log('ID serializado:', message.id?._serialized || 'não encontrado');
      const media = await message.downloadMedia();
      console.log('MIME recebido:', media?.mimetype);

      if (media && media.mimetype && media.mimetype.startsWith('audio/')) {
        const audioBuffer = Buffer.from(media.data, 'base64');
        console.log('Áudio baixado:', audioBuffer.length, 'bytes');

        if (audioBuffer.length <= 10 * 1024 * 1024) {
          payload.audio_base64 = media.data;
          payload.audio_mimetype = media.mimetype.split(';')[0].trim();
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

    console.log('Enviando para Django...');
    const { data } = await axios.post(WEBHOOK_URL, payload, {
      maxContentLength: 20 * 1024 * 1024,
      maxBodyLength: 20 * 1024 * 1024,
      timeout: 120000,
    });

    console.log('Resposta do Django:', data);
    if (data.resposta) await message.reply(data.resposta);
  } catch (error) {
    console.error('========== ERRO NO WEBHOOK ==========');
    console.error('Mensagem:', error.message);
    console.error('Status:', error.response?.status);
    console.error('Resposta:', error.response?.data);
    console.error('Stack:', error.stack);
    console.error('=====================================');
    await message.reply('Não consegui registrar seu gasto agora. Tente novamente.');
  }
});

client.initialize();
