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

beforeEach(() => {
  frontendErrors.length = 0
  cy.task('resetBackendErrors', null, { log: false })

  // Mock auth/me endpoint — the app calls this on every page load.
  // Without auth enabled on the backend the request hangs or 404s,
  // blocking the entire UI from rendering.
  cy.intercept('GET', '**/auth/me', {
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

  // Mock global endpoints that are called on every page load.
  // Without these, failed API calls trigger Vue's errorHandler which
  // shows a persistent error dialog that blocks all UI interaction.
  cy.intercept('GET', '**/knowledge_sources/plugins', {
    statusCode: 200,
    body: [],
  }).as('ksPlugins')

  cy.intercept('GET', '**/admin/catalog**', (req) => {
    req.on('response', (res) => {
      // Let successful responses through, mock only failures
      if (res.statusCode >= 400) {
        res.send({ statusCode: 200, body: { items: [], total: 0, limit: 20, offset: 0 } })
      }
    })
  })

  // Mock auth/refresh to prevent token refresh loops that trigger login redirect
  cy.intercept('POST', '**/auth/refresh', {
    statusCode: 200,
    body: { access_token: 'e2e-fake-token', token_type: 'bearer' },
  }).as('authRefresh')

  // Catch any API errors that would trigger the error dialog or login redirect.
  // Convert 401/5xx to safe 200 responses so tests can exercise the UI.
  // NOTE: For full CRUD testing, run the backend with AUTH_ENABLED=false.
  cy.intercept({ url: '**/api/**' }, (req) => {
    req.on('response', (res) => {
      if (res.statusCode === 401 || res.statusCode >= 500) {
        const isWrite = ['POST', 'PUT', 'PATCH'].includes(req.method)
        const body = isWrite
          ? { id: '00000000-0000-0000-0000-000000000001', name: 'e2e-mocked' }
          : { items: [], total: 0, limit: 20, offset: 0 }
        res.send({ statusCode: 200, body })
      }
    })
  })
})

afterEach(function () {
  const testTitle = this.currentTest?.fullTitle() ?? 'unknown'
  const testFile = (this.currentTest as Cypress.TestResult & { invocationDetails?: { relativeFile?: string } })
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
