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

  // Mock auth/me endpoint to prevent the app from hanging when AUTH_ENABLED=false
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
