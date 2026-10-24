import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: false,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: { baseURL: 'http://localhost:3000' },
  // 214 specs across checkout/, account/, search/, admin/
});
