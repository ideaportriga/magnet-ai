import './commands'

// ─── Types ──────────────────────────────────────────────────────────────────

interface FrontendError {
  type: 'console.error' | 'console.warn' | 'uncaught'
  message: string
  stack?: string
  timestamp: string
}

// ─── State ───────────────────────────────────────────────────────────────────

const frontendErrors: FrontendError[] = []

// ─── Browser error capture ───────────────────────────────────────────────────

// Intercept console.error and console.warn before each test's page load
Cypress.on('window:before:load', (win) => {
  const originalError = win.console.error.bind(win.console)
  win.console.error = (...args: unknown[]) => {
    frontendErrors.push({
      type: 'console.error',
      message: args.map((a) => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' '),
      timestamp: new Date().toISOString(),
    })
    originalError(...args)
  }

  const originalWarn = win.console.warn.bind(win.console)
  win.console.warn = (...args: unknown[]) => {
    frontendErrors.push({
      type: 'console.warn',
      message: args.map((a) => (typeof a === 'object' ? JSON.stringify(a) : String(a))).join(' '),
      timestamp: new Date().toISOString(),
    })
    originalWarn(...args)
  }
})

// Capture unhandled JS exceptions — don't fail the test immediately,
// we'll collect and report them in afterEach
Cypress.on('uncaught:exception', (err) => {
  frontendErrors.push({
    type: 'uncaught',
    message: err.message,
    stack: err.stack,
    timestamp: new Date().toISOString(),
  })
  return false
})

// ─── Per-test hooks ──────────────────────────────────────────────────────────

// Local-auth credentials for the E2E test user. Created idempotently by
// the `ensureLoggedIn` helper below via `/api/v2/auth/signup` on the first
// spec run and reused after.
const E2E_EMAIL = Cypress.env('e2eEmail') || 'e2e@test.local'
const E2E_PASSWORD = Cypress.env('e2ePassword') || 'E2eTest!pass123'

/**
 * Sign up (if needed) and log in the E2E user via the real backend. Uses
 * `cy.session()` so the login HTTP round-trip happens at most once per
 * spec; subsequent tests reuse the cached auth cookies.
 *
 * Requires backend running with `AUTH_PROVIDERS` including `local`.
 */
// Cypress baseUrl is the frontend `/admin/` subpath, but the Vite dev
// server proxies `/api` only from the port root — not from `/admin/api`.
// Use absolute paths relative to the dev-server origin so auth endpoints
// actually reach the backend.
const DEV_ORIGIN = 'https://localhost:7001'

function ensureLoggedIn() {
  // Promote runs unconditionally (not inside cy.session's cached body) so
  // a previously-cached session on a not-yet-promoted user still gets its
  // flags flipped. `/test/promote` is idempotent.
  cy.request({
    method: 'POST',
    url: `${DEV_ORIGIN}/test/promote`,
    body: { email: E2E_EMAIL },
    failOnStatusCode: false,
  })
  cy.session(
    ['e2e-local-v2', E2E_EMAIL],
    () => {
      // Signup — best-effort. 409 = user already exists, which is fine.
      cy.request({
        method: 'POST',
        url: `${DEV_ORIGIN}/api/v2/auth/signup`,
        body: { email: E2E_EMAIL, password: E2E_PASSWORD, name: 'E2E Test User' },
        failOnStatusCode: false,
      })
      // Promote again inside the session block (covers first-run case where
      // user didn't exist yet before the outer promote call).
      cy.request({
        method: 'POST',
        url: `${DEV_ORIGIN}/test/promote`,
        body: { email: E2E_EMAIL },
        failOnStatusCode: false,
      })
      // Login — this sets the httpOnly auth cookies on the browser.
      cy.request({
        method: 'POST',
        url: `${DEV_ORIGIN}/api/v2/auth/login`,
        body: { email: E2E_EMAIL, password: E2E_PASSWORD },
        failOnStatusCode: false,
      }).then((res) => {
        if (res.status !== 200 && res.status !== 201) {
          throw new Error(
            `[ensureLoggedIn] login failed (${res.status}) — make sure the ` +
            `backend is running with AUTH_PROVIDERS=...,local and DEBUG_MODE=true. ` +
            `Response body: ${JSON.stringify(res.body)}`,
          )
        }
      })
    },
    {
      // Session is valid if /auth/me returns 200
      validate() {
        cy.request({ url: `${DEV_ORIGIN}/api/v2/auth/me`, failOnStatusCode: false }).then((res) => {
          expect([200, 304]).to.include(res.status)
        })
      },
      cacheAcrossSpecs: true,
    },
  )
}

beforeEach(() => {
  frontendErrors.length = 0
  cy.task('resetBackendErrors', null, { log: false })

  // Real-auth mode (default): sign up + log in once per session via the
  // local provider, then let the real /api/v2/auth/me response flow through.
  // Mocked-auth mode (`CYPRESS_MOCK_API=true`): no login, stub /auth/me.
  if (Cypress.env('MOCK_API')) {
    cy.intercept('GET', '**/api/v2/auth/me', {
      statusCode: 200,
      body: {
        id: 'e2e-test-user',
        email: 'e2e@test.com',
        name: 'E2E Test User',
        preferred_username: 'e2e@test.com',
        is_active: true,
        is_superuser: true,
        is_verified: true,
        roles: ['admin'],
      },
    }).as('authMe')
  } else {
    ensureLoggedIn()
  }

  // MOCK_API-only safety nets. In real-auth mode these go through the
  // backend untouched so tests exercise real data.
  if (Cypress.env('MOCK_API')) {
    cy.intercept('GET', '**/knowledge_sources/plugins', {
      statusCode: 200,
      body: [],
    }).as('ksPlugins')

    cy.intercept('GET', '**/admin/catalog**', (req) => {
      req.on('response', (res) => {
        if (res.statusCode >= 400) {
          res.send({ statusCode: 200, body: [] })
        }
      })
    })

    cy.intercept('POST', '**/api/v2/auth/refresh', {
      statusCode: 200,
      body: { access_token: 'e2e-fake-token', token_type: 'bearer' },
    }).as('authRefresh')
  }

  // §I.5 — real-backend profile. The aggressive catch-all `401|5xx → 200`
  // mock was removed: it hid real backend bugs and made CRUD tests "green"
  // even when create/update endpoints were returning 500. Run the backend
  // with `AUTH_ENABLED=false` (or supply a real bearer token) so real
  // responses reach the UI.
  //
  // Opt-in mock for CI-without-backend: set `CYPRESS_MOCK_API=true` to
  // restore the old behaviour.
  if (Cypress.env('MOCK_API')) {
    cy.intercept({ url: '**/api/**' }, (req) => {
      req.on('response', (res) => {
        if (res.statusCode === 401 || res.statusCode >= 500) {
          const isWrite = ['POST', 'PUT', 'PATCH'].includes(req.method)
          // Catalog endpoint returns a flat array, not a paginated object.
          const isCatalog = /\/admin\/catalog(\?|$)/.test(req.url)
          const body = isWrite
            ? { id: '00000000-0000-0000-0000-000000000001', name: 'e2e-mocked' }
            : isCatalog
              ? []
              : { items: [], total: 0, limit: 20, offset: 0 }
          res.send({ statusCode: 200, body })
        }
      })
    })
  }
})

// Global cleanup: after every spec file, wipe e2e-test-* records so the
// next spec starts from a clean baseline. Best-effort — if the backend
// cleanup endpoint is unavailable (not in DEBUG_MODE) it logs and continues.
after(() => {
  cy.cleanup('e2e-test-')
})

afterEach(function () {
  const testTitle = this.currentTest?.fullTitle() ?? 'unknown'
  const testFile = (this.currentTest as Mocha.Test & { invocationDetails?: { relativeFile?: string } })
    ?.invocationDetails?.relativeFile ?? 'unknown'
  const testStatus = this.currentTest?.state ?? 'unknown'
  const timestamp = new Date().toISOString()

  // Snapshot frontend errors (array will be reset on next beforeEach)
  const capturedFrontend = [...frontendErrors]

  cy.task('getBackendErrors', null, { log: false }).then((backendErrors) => {
    const be = backendErrors as unknown[]

    // Save report whenever errors exist OR the test failed
    if (capturedFrontend.length > 0 || be.length > 0 || testStatus === 'failed') {
      cy.task('saveTestReport', {
        testTitle,
        testFile,
        testStatus,
        frontendErrors: capturedFrontend,
        backendErrors: be,
        timestamp,
      })
    }
  })
})
