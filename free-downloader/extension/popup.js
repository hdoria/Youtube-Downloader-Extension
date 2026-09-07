const form = document.querySelector('#download-form');
const url = document.querySelector('#url');
const button = document.querySelector('#download');
const progress = document.querySelector('#progress');
const status = document.querySelector('#status');

function render(state) {
  button.disabled = state.status === 'running';
  progress.hidden = state.status !== 'running';
  progress.value = Number.isFinite(state.percent) ? state.percent : 0;
  status.textContent = state.message + (state.filename ? ` ${state.filename}` : '');
}
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'state') render(message.state);
});
chrome.runtime.sendMessage({ type: 'getState' }).then(render);
chrome.tabs.query({ active: true, currentWindow: true }).then(([tab]) => {
  if (tab?.url && /^https:\/\/(www\.|m\.)?youtube\.com\/|^https:\/\/youtu\.be\//.test(tab.url)) url.value = tab.url;
});
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const result = await chrome.runtime.sendMessage({ type: 'download', url: url.value.trim(), quality: document.querySelector('#quality').value });
  if (result.error) status.textContent = result.error;
});
