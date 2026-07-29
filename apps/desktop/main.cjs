const { app, BrowserWindow } = require('electron');
const { spawn } = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '../..');
let apiProcess = null;

function startApi() {
  apiProcess = spawn('python', ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8791'], {
    cwd: root,
    shell: true,
    windowsHide: true,
    stdio: 'inherit',
  });
}

async function isApiUp() {
  try {
    const response = await fetch('http://127.0.0.1:8791/api/health');
    return response.ok;
  } catch (_error) {
    return false;
  }
}

async function waitForApi() {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    if (await isApiUp()) return;
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
}

async function createWindow() {
  if (!(await isApiUp())) {
    startApi();
  }
  await waitForApi();
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1180,
    minHeight: 760,
    title: 'Video Text Translator',
    backgroundColor: '#111316',
    webPreferences: {
      contextIsolation: true,
    },
  });
  const builtIndex = path.join(root, 'dist', 'client', 'index.html');
  if (process.env.VTT_UI_URL) {
    await win.loadURL(process.env.VTT_UI_URL);
  } else if (require('node:fs').existsSync(builtIndex)) {
    await win.loadFile(builtIndex);
  } else {
    await win.loadURL('http://127.0.0.1:8790');
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (apiProcess) {
    apiProcess.kill();
  }
  if (process.platform !== 'darwin') app.quit();
});
