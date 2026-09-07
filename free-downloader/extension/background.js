const HOST = 'com.hdoria.free_video_downloader';
let nativePort = null;
let state = { status: 'idle', message: 'Abra um vídeo ou cole o link abaixo.' };
const ready = chrome.storage.session.get('download').then(({ download }) => {
  if (download && !nativePort) {
    state = download.status === 'running'
      ? { status: 'error', message: 'A conexão anterior foi interrompida. Tente novamente.' }
      : download;
  }
});

function update(next) {
  state = next;
  chrome.storage.session.set({ download: state });
  chrome.runtime.sendMessage({ type: 'state', state }).catch(() => {});
}

chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (sender.id !== chrome.runtime.id) return;
  ready.then(() => {
    if (message.type === 'getState') {
      reply(state);
      return;
    }
    if (message.type !== 'download') {
      reply({ error: 'Pedido inválido.' });
      return;
    }
    if (nativePort) {
      reply({ error: 'Aguarde o download atual terminar.' });
      return;
    }
    update({ status: 'running', message: 'Conectando ao auxiliar local…', percent: 0 });
    try {
      const port = chrome.runtime.connectNative(HOST);
      nativePort = port;
      port.onMessage.addListener((result) => {
        if (!['running', 'done', 'error'].includes(result.status)) return;
        update(result);
        if (result.status !== 'running') {
          nativePort = null;
          port.disconnect();
        }
      });
      port.onDisconnect.addListener(() => {
        const disconnectedWithError = chrome.runtime.lastError;
        if (nativePort !== port) return;
        nativePort = null;
        update({ status: 'error', message: disconnectedWithError
          ? 'Auxiliar indisponível. Confira a instalação e o ID da extensão no README.'
          : 'A conexão com o auxiliar foi interrompida.' });
      });
      port.postMessage({ action: 'download', url: message.url, quality: message.quality });
      reply({ ok: true });
    } catch {
      nativePort = null;
      update({ status: 'error', message: 'Não foi possível iniciar o auxiliar local.' });
      reply({ error: state.message });
    }
  });
  return true;
});
