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
 

test('edit a todo title', async ({ page }) => {
  await page.goto('/');

  const original = `Edit me ${Date.now()}`;
  const updated = `${original} - updated`;

  // Add a todo
  await page.locator('[data-testid="todo-input"]').fill(original);
  await page.locator('[data-testid="todo-add"]').click();

  // Locate the row by original title
  const item = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: original }),
  });
  await expect(item).toHaveCount(1);

  // Fill the inline edit input and save
  await item.locator('input[name="title"]').fill(updated);
  await item.locator('[data-testid="todo-edit"]').click();

  // Verify the updated title is rendered
  const updatedItem = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: updated }),
  });
  await expect(updatedItem).toHaveCount(1);
});


test('delete a todo', async ({ page }) => {
  await page.goto('/');

  const title = `Delete me ${Date.now()}`;
  await page.locator('[data-testid="todo-input"]').fill(title);
  await page.locator('[data-testid="todo-add"]').click();

  const item = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: title }),
  });
  await expect(item).toHaveCount(1);

  // Accept confirm dialog and click delete
  const once = page.once('dialog', d => d.accept());
  await item.locator('[data-testid="todo-delete"]').click();
  await once; // ensure dialog was handled

  // Verify it is gone
  const deleted = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: title }),
  });
  await expect(deleted).toHaveCount(0);
});


test('edit with invalid title (spaces) is rejected', async ({ page }) => {
  await page.goto('/');

  const original = `Keep me ${Date.now()}`;
  await page.locator('[data-testid="todo-input"]').fill(original);
  await page.locator('[data-testid="todo-add"]').click();

  const item = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: original }),
  });
  await expect(item).toHaveCount(1);

  // Fill spaces; browser will allow since minlength=1, but server trims and rejects
  await item.locator('input[name="title"]').fill('   ');
  await item.locator('[data-testid="todo-edit"]').click();

  // After submit, title should remain unchanged
  const unchanged = page.locator('[data-testid="todo-item"]', {
    has: page.locator('[data-testid="todo-title"]', { hasText: original }),
  });
  await expect(unchanged).toHaveCount(1);
});
 
test('filters and sorting work independently', async ({ page, request }) => {
  await page.goto('/');

  // Create a few via API for deterministic setup
  await request.post('/api/todos', { data: { title: 'Older high', priority: 'high' } });
  // Wait briefly to ensure created_at order
  await page.waitForTimeout(50);
  await request.post('/api/todos', { data: { title: 'Newest low', priority: 'low' } });

  // Apply priority filter = low
  await page.selectOption('form#filters select[name="p"]', 'low');
  await page.click('form#filters button[type="submit"]');
  await expect(page.locator('[data-testid="todo-item"]')).toHaveCount(1);
  await expect(page.getByText('Newest low')).toBeVisible();

  // Clear priority filter and sort oldest
  await page.selectOption('form#filters select[name="p"]', 'all');
  await page.selectOption('form#filters select[name="sort"]', 'created');
  await page.click('form#filters button[type="submit"]');

  // Oldest should appear before newest - check first item contains 'Older high'
  const firstItem = page.locator('[data-testid="todo-item"]').first();
  await expect(firstItem.getByText('Older high')).toBeVisible();
});
