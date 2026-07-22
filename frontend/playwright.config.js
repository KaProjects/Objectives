const {defineConfig, devices} = require('@playwright/test')

module.exports = defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.js',
  outputDir: './test-results',
  fullyParallel: true,
  forbidOnly: true,
  reporter: [
    ['list'],
    ['html', {open: 'never'}],
  ],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4173',
    env: {
      ...process.env,
      VITE_BACKEND_URL: '/api',
    },
    reuseExistingServer: true,
    url: 'http://127.0.0.1:4173',
  },
  projects: [
    {
      name: 'chromium',
      use: {...devices['Desktop Chrome']},
    },
  ],
})
