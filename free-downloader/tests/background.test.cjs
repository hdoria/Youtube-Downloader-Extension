const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

function setup() {
  let listener;
  let onNativeMessage;
  let onDisconnect;
  const requests = [];
  const updates = [];
  let disconnected = false;
  const port = {
    onMessage: { addListener(fn) { onNativeMessage = fn; } },
    onDisconnect: { addListener(fn) { onDisconnect = fn; } },
    postMessage(message) { requests.push(message); },
    disconnect() { disconnected = true; onDisconnect(); },
  };
  const chrome = {
    storage: { session: { get: async () => ({}), set: async () => {} } },
    runtime: {
      id: 'test-extension',
      onMessage: { addListener(fn) { listener = fn; } },
      sendMessage: async (message) => { updates.push(message); throw new Error('Popup is closed'); },
      connectNative: () => port,
    },
  };
  vm.runInNewContext(fs.readFileSync(__dirname + '/../extension/background.js', 'utf8'), { chrome });
  return {
    request: (message) => new Promise((resolve) => listener(message, { id: chrome.runtime.id }, resolve)),
    emit: (message) => onNativeMessage(message),
    disconnect: () => onDisconnect(),
    requests, updates,
    isDisconnected: () => disconnected,
  };
}

test('download persists without popup and state is available when reopened', async () => {
  const app = setup();
  assert.equal((await app.request({ type: 'download', url: 'https://youtu.be/AbCdEf012_-', quality: '2160' })).ok, true);
  assert.equal(app.requests.length, 1);
  app.emit({ status: 'running', message: 'Baixando', percent: 45 });
  assert.equal(app.isDisconnected(), false);
  assert.equal((await app.request({ type: 'getState' })).percent, 45);
  assert.ok((await app.request({ type: 'download' })).error);
  app.emit({ status: 'done', message: 'Salvo', filename: 'video.mkv' });
  assert.equal(app.isDisconnected(), true);
  assert.equal((await app.request({ type: 'getState' })).status, 'done');
});

test('unexpected host disconnect clears running state', async () => {
  const app = setup();
  await app.request({ type: 'download', url: 'https://youtu.be/AbCdEf012_-', quality: '1080' });
  app.disconnect();
  assert.equal((await app.request({ type: 'getState' })).status, 'error');
});
