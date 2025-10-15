// tests/e2e/todo.spec.ts
import { test, expect } from '@playwright/test';

test.beforeEach(async ({ request }) => {
  // Reset all todos if TEST_RESET=1 (ignore 403 otherwise)
  await request.post('/api/_reset').catch(() => {});
});

test('add and toggle a todo', async ({ page }) => {
  await page.goto('/');

  const title = `Buy milk ${Date.now()}`; // unique title per run

  // Fill and submit new todo
  await page.locator('[data-testid="todo-input"]').fill(title);
  await page.locator('[data-testid="todo-add"]').click();

  // Find the specific todo-item that contains our title
  const item = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: title }),
  });

  // Sanity check: ensure only one match and visible
  await expect(item).toHaveCount(1);
  await expect(item).toBeVisible();

  // Click the toggle button inside that same row
  await item.locator('[data-testid="todo-toggle"]').click();

  // Verify that its title span now has the "done" class
  const titleSpan = item.locator('[data-testid="todo-title"]');
  await expect(titleSpan).toHaveClass(/(^|\s)done(\s|$)/);
});



