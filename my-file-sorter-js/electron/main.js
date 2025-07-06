const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const isDev = require('electron-is-dev');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, '../react-ui/build/index.html')}`;

  win.loadURL(startUrl);

  if (isDev) {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

ipcMain.handle('dialog:openDirectory', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  return canceled ? null : filePaths[0];
});

ipcMain.handle('files:getTriageList', async (event, dirPath) => {
  try {
    const files = await fs.readdir(dirPath);
    const detailedFiles = await Promise.all(
      files.map(async (file) => {
        const fullPath = path.join(dirPath, file);
        const stat = await fs.stat(fullPath);
        if (stat.isDirectory()) return null;
        return {
          id: fullPath,
          name: file,
          path: fullPath,
          size: stat.size,
          lastModified: stat.mtimeMs,
          createdAt: stat.birthtimeMs,
        };
      })
    );
    const validFiles = detailedFiles.filter(Boolean);
    validFiles.sort((a, b) => a.lastModified - b.lastModified || b.size - a.size);
    return { success: true, files: validFiles };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('files:performAction', async (event, { action, path: filePath, newName }) => {
  try {
    if (action === 'delete') {
      await fs.unlink(filePath);
      return { success: true, message: `Deleted ${path.basename(filePath)}` };
    }

    if (action === 'rename') {
      if (!newName) throw new Error('New name not provided for rename.');
      const dirName = path.dirname(filePath);
      const newPath = path.join(dirName, newName);
      await fs.rename(filePath, newPath);
      return { success: true, message: `Renamed to ${newName}` };
    }

    if (action === 'sort') {
      const extensionMap = {
        '.pdf': 'Documents', '.docx': 'Documents', '.txt': 'Documents',
        '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images',
        '.mp4': 'Videos', '.mov': 'Videos', '.mkv': 'Videos',
        '.mp3': 'Music', '.wav': 'Music',
        '.py': 'Development', '.js': 'Development', '.html': 'Development',
      };
      const fileName = path.basename(filePath);
      const fileExt = path.extname(fileName).toLowerCase();
      const targetFolder = extensionMap[fileExt] || 'Other';
      const baseDir = path.dirname(filePath);
      const targetDir = path.join(baseDir, targetFolder);
      await fs.mkdir(targetDir, { recursive: true });
      const newPath = path.join(targetDir, fileName);
      await fs.rename(filePath, newPath);
      return { success: true, message: `Sorted ${fileName} to ${targetFolder}` };
    }

    throw new Error('Invalid action specified.');
  } catch (error) {
    return { success: false, error: error.message };
  }
});
