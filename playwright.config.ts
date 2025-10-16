// @ts-nocheck
import { defineConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';

// Prefer the workspace virtualenv's Python to ensure Flask is available.
const isWin = process.platform === 'win32';
const venvPython = path.resolve(__dirname, '.venv', isWin ? 'Scripts' : 'bin', isWin ? 'python.exe' : 'python');
const venvBin = path.dirname(venvPython);
const hasVenvPython = fs.existsSync(venvPython);
const webCommand = hasVenvPython ? `"${venvPython}" -m flask run` : 'python -m flask run';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://127.0.0.1:5000',
    headless: true,
  },
  webServer: {
    command: webCommand,
    port: 5000,
    reuseExistingServer: true,
    env: {
      FLASK_APP: 'app:create_app',
      FLASK_ENV: 'development',
      FLASK_DEBUG: '1',
      TEST_RESET: '1',
      // Ensure the venv bin directory is at the front of PATH if available
      PATH: (hasVenvPython ? `${venvBin}${path.delimiter}` : '') + (process.env.PATH ?? ''),
    },
  },
});
