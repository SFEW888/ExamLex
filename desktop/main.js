const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let mainWindow;
let pythonProcess;
const BACKEND_PORT = 8765;

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    title: 'ExamLex - AI 驱动的英语备考系统',
    icon: path.join(__dirname, '../public/logo.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    autoHideMenuBar: true, // 隐藏菜单栏
    show: false // 先不显示，等加载完成
  });

  // 显示加载页面
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // 启动 Python 后端
  startPythonBackend();

  // 窗口关闭时清理
  mainWindow.on('closed', () => {
    mainWindow = null;
    stopPythonBackend();
  });
}

// 启动 Python 后端
function startPythonBackend() {
  console.log('正在启动 Python 后端...');

  // Python 可执行文件路径
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';

  // 项目根目录
  const projectRoot = path.join(__dirname, '..');

  // 启动本地标准库 Web 服务，避免桌面端依赖 uvicorn/FastAPI 才能打开。
  pythonProcess = spawn(pythonPath, [
    '-m', 'skills.examlex.scripts.web_app',
    '--host', '127.0.0.1',
    '--port', BACKEND_PORT.toString(),
    '--data-dir', path.join(app.getPath('userData'), 'data')
  ], {
    cwd: projectRoot,
    env: { ...process.env }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python 进程退出，代码: ${code}`);
  });

  // 等待后端启动
  waitForBackend();
}

// 等待后端启动完成
async function waitForBackend() {
  const maxRetries = 30; // 最多等待 30 秒
  let retries = 0;

  const checkBackend = async () => {
    try {
      const response = await axios.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, {
        timeout: 1000
      });

      if (response.status === 200) {
        console.log('✅ Python 后端启动成功！');

        // 加载主页面
        const frontendUrl = process.argv.includes('--dev') ? 'http://127.0.0.1:5173' : `http://127.0.0.1:${BACKEND_PORT}`;
        if (frontendUrl.startsWith('http')) mainWindow.loadURL(frontendUrl);
        else mainWindow.loadFile(path.join(__dirname, '../skills/examlex/assets/web/index.html'));

        return true;
      }
    } catch (error) {
      retries++;

      if (retries >= maxRetries) {
        console.error('❌ Python 后端启动失败！');

        // 显示错误页面
        mainWindow.loadFile(path.join(__dirname, 'error.html'));
        return false;
      }

      // 继续等待
      setTimeout(checkBackend, 1000);
    }
  };

  checkBackend();
}

// 停止 Python 后端
function stopPythonBackend() {
  if (pythonProcess) {
    console.log('正在停止 Python 后端...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

// 应用准备就绪
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// 所有窗口关闭时退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 应用退出前清理
app.on('before-quit', () => {
  stopPythonBackend();
});

// IPC 通信处理
ipcMain.handle('get-backend-url', () => {
  return `http://127.0.0.1:${BACKEND_PORT}`;
});

ipcMain.handle('check-backend-status', async () => {
  try {
    const response = await axios.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, {
      timeout: 2000
    });
    return { status: 'online', data: response.data };
  } catch (error) {
    return { status: 'offline', error: error.message };
  }
});
