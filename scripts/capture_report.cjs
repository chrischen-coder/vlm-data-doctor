// Optional visual QA tooling: npm install --no-save --package-lock=false playwright
// Then: npx playwright install chromium && node scripts/capture_report.cjs
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const options = { headless: true };
  if (process.env.VLM_DOCTOR_BROWSER) options.executablePath = process.env.VLM_DOCTOR_BROWSER;
  const browser = await chromium.launch(options);
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 1160 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    let networkRequests = 0;
    page.on('request', request => { if (/^https?:/.test(request.url())) networkRequests += 1; });
    await page.goto(pathToFileURL(path.join(root, 'docs/demo/report.html')).href);
    await page.getByText('4 findings shown', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Warnings', exact: true }).click();
    await page.getByText('1 finding shown', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Errors', exact: true }).click();
    await page.getByText('3 findings shown', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'All findings', exact: true }).click();
    await page.getByRole('searchbox', { name: 'Search findings' }).fill('missing_image');
    await page.getByText('1 finding shown', { exact: true }).waitFor();
    await page.getByRole('searchbox', { name: 'Search findings' }).fill('no-such-rule');
    await page.getByText('No findings match this view.', { exact: true }).waitFor();
    await page.getByRole('searchbox', { name: 'Search findings' }).fill('');
    await page.getByText('4 findings shown', { exact: true }).waitFor();
    await page.getByRole('heading', { name: 'Dataset preflight.' }).click();
    await page.screenshot({ path: path.join(root, 'docs/assets/report-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(root, 'docs/assets/report-mobile.png'), fullPage: false });
    await page.getByRole('heading', { name: 'Review queue' }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(root, 'docs/assets/report-mobile-details.png'), fullPage: false });
    if (horizontalOverflow || errors.length || networkRequests) {
      throw new Error(JSON.stringify({ horizontalOverflow, errors, networkRequests }));
    }
    const results = { browser: browser.version(), desktop: '1200x1160', mobile: '390x844',
      severityFilters: 'passed', textSearch: 'passed', emptyState: 'passed',
      pageErrors: errors, externalNetworkRequests: networkRequests, mobilePageOverflow: horizontalOverflow };
    fs.writeFileSync(path.join(root, 'benchmarks/results/report-ui.json'), JSON.stringify(results, null, 2) + '\n');
    console.log(JSON.stringify(results));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
