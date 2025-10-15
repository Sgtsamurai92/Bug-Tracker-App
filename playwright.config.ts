import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://127.0.0.1:5000',
    headless: true,
  },
  webServer: {
    command: 'python -m flask run',
    port: 5000,
    reuseExistingServer: true,
    env: {
      FLASK_APP: 'app:create_app',
      FLASK_ENV: 'development',
      FLASK_DEBUG: '1',
      TEST_RESET: '1',
    },
  },
});


