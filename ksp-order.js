const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  try {
    // Step 1: Go to product page
    const sku = '370601';
    console.log(`[1] Navigating to product ${sku}...`);
    await page.goto(`https://ksp.co.il/web/cat/item/${sku}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    const title = await page.title();
    console.log(`[1] Page title: ${title}`);
    await page.screenshot({ path: '/tmp/ksp-1-product.png' });

    // Step 2: Login via auth.ksp.co.il
    console.log('[2] Going to login...');
    await page.goto('https://auth.ksp.co.il/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/ksp-2-login.png' });

    // Enter email
    console.log('[2] Entering email...');
    await page.fill('input[name="email"]', 'joni.avni@gmail.com');
    await page.screenshot({ path: '/tmp/ksp-2b-email.png' });

    // Click "המשך עם סיסמה" (continue with password)
    console.log('[2] Clicking password button...');
    const passwordBtn = page.locator('button[aria-label="המשך באמצעות גוגל"]').first();
    // Actually look for "המשך עם סיסמה"
    const allButtons = await page.locator('button').all();
    for (const btn of allButtons) {
      const text = await btn.textContent();
      if (text && text.includes('סיסמה')) {
        console.log('[2] Found password button:', text.trim());
        await btn.click();
        break;
      }
    }
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/ksp-2c-after-password-click.png' });

    // Enter password
    console.log('[2] Entering password...');
    const passInput = page.locator('input[type="password"]');
    await passInput.waitFor({ timeout: 5000 });
    await passInput.fill('Aa12141618');
    await page.screenshot({ path: '/tmp/ksp-2d-password.png' });

    // Submit login
    console.log('[2] Submitting login...');
    await passInput.press('Enter');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/tmp/ksp-2e-after-login.png' });
    console.log('[2] After login URL:', page.url());

    // Step 3: Go to product page
    console.log(`[3] Going to product ${sku}...`);
    await page.goto(`https://ksp.co.il/web/cat/item/${sku}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/ksp-3-product.png' });

    const productTitle = await page.title();
    console.log('[3] Product page:', productTitle);

    // Step 4: Add to cart
    console.log('[4] Looking for add to cart button...');
    const addToCartSelectors = [
      'button:has-text("הוסף לסל")',
      'button:has-text("לסל")',
      '[data-testid="add-to-cart"]',
      '.add-to-cart',
      'button.buy-button',
    ];
    
    let added = false;
    for (const sel of addToCartSelectors) {
      try {
        const btn = page.locator(sel).first();
        const count = await btn.count();
        if (count > 0) {
          console.log(`[4] Found button with selector: ${sel}`);
          await btn.click();
          added = true;
          break;
        }
      } catch (e) {}
    }

    if (!added) {
      // Try finding by text
      const buttons = await page.locator('button').all();
      for (const btn of buttons) {
        const text = await btn.textContent();
        if (text && (text.includes('סל') || text.includes('קנה') || text.includes('רכוש'))) {
          console.log('[4] Found button:', text.trim());
          await btn.click();
          added = true;
          break;
        }
      }
    }

    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/ksp-4-added-to-cart.png' });
    console.log('[4] Add to cart attempted:', added);

    // Step 5: Go to cart
    console.log('[5] Going to cart...');
    await page.goto('https://ksp.co.il/web/cart', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/tmp/ksp-5-cart.png' });
    console.log('[5] Cart URL:', page.url());

    // Step 6: Checkout
    console.log('[6] Looking for checkout button...');
    const checkoutSelectors = [
      'button:has-text("לתשלום")',
      'button:has-text("תשלום")',
      'a:has-text("לתשלום")',
      '[data-testid="checkout"]',
    ];

    let checkedOut = false;
    for (const sel of checkoutSelectors) {
      try {
        const btn = page.locator(sel).first();
        const count = await btn.count();
        if (count > 0) {
          console.log(`[6] Found checkout with: ${sel}`);
          await btn.click();
          checkedOut = true;
          break;
        }
      } catch (e) {}
    }

    await page.waitForTimeout(3000);
    await page.screenshot({ path: '/tmp/ksp-6-checkout.png' });
    console.log('[6] Checkout URL:', page.url());

    // Step 7: Complete order (if saved payment available)
    console.log('[7] Looking for complete order / pay button...');
    await page.screenshot({ path: '/tmp/ksp-7-payment.png' });
    
    const pageContent = await page.content();
    const pageText = await page.evaluate(() => document.body.innerText);
    console.log('[7] Page text snippet:', pageText.substring(0, 500));

  } catch (err) {
    console.error('Error:', err.message);
    await page.screenshot({ path: '/tmp/ksp-error.png' });
  } finally {
    await browser.close();
  }
})();
