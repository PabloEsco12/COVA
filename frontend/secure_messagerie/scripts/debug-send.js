import { chromium } from "playwright"

;(async () => {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  page.setDefaultTimeout(15000)
  page.on('console', (msg) => {
    console.log(`[console:${msg.type()}] ${msg.text()}`)
  })
  page.on('pageerror', (err) => {
    console.error('[pageerror]', err)
  })
  await page.goto('http://localhost:5176/login')
  await page.fill('input[autocomplete="username"]', 'alice@example.com')
  await page.fill('input[autocomplete="current-password"]', 'Password123!')
  await Promise.all([
    page.waitForURL('**/dashboard**', { timeout: 15000 }),
    page.click('button:has-text("Se connecter")'),
  ])
  await page.goto('http://localhost:5176/dashboard/messages')
  await page.waitForSelector('.msg-nav__item', { timeout: 15000 })
  await page.getByRole('button', { name: /test chat/i }).click()
  await page.waitForSelector('textarea.form-control', { timeout: 15000 })
  await page.fill('textarea.form-control', 'Playwright message at ' + new Date().toISOString())
  const postPromise = page
    .waitForResponse(
      (response) =>
        response.request().method() === 'POST' && /\/api\/conversations\/.+\/messages/.test(response.url()),
      { timeout: 5000 },
    )
    .catch((err) => err)
  await page.click('button:has-text("Envoyer")')
  const postResponse = await postPromise
  if (postResponse instanceof Error) {
    console.error('No POST request observed:', postResponse.message)
  } else {
    console.log('POST status:', postResponse.status(), postResponse.url())
  }
  await browser.close()
})()
