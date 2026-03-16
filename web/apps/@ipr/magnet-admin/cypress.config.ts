import * as fs from 'node:fs'
import * as http from 'node:http'
import * as path from 'node:path'

import { nxE2EPreset } from '@nx/cypress/plugins/cypress-preset'
import { defineConfig } from 'cypress'

// ─── Config ──────────────────────────────────────────────────────────────────

const BACKEND_URL = 'http://localhost:8000'
// Resolve to project root (magnet-ai/reports)
const REPORTS_DIR = path.resolve(__dirname, '../../../..', 'reports')

// ─── Helpers ─────────────────────────────────────────────────────────────────

function sanitizeName(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9\s]/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
    .toLowerCase()
    .slice(0, 80)
}

function httpGet(url: string): Promise<unknown[]> {
  return new Promise((resolve) => {
    http
      .get(url, (res) => {
        let data = ''
        res.on('data', (chunk: string) => (data += chunk))
        res.on('end', () => {
          try {
            const parsed = JSON.parse(data)
            resolve(Array.isArray(parsed) ? parsed : [])
          } catch {
            resolve([])
          }
        })
      })
      .on('error', () => resolve([]))
  })
}

function httpPost(url: string): Promise<void> {
  return new Promise((resolve) => {
    const req = http.request(url, { method: 'POST' }, () => resolve())
    req.on('error', () => resolve())
    req.end()
  })
}

// ─── Report generators ───────────────────────────────────────────────────────

interface FrontendError {
  type: string
  message: string
  stack?: string
  timestamp: string
}

interface BackendError {
  level: string
  event: string
  timestamp: string
  filename: string
  func_name: string
  lineno: string | number
  traceback?: string
}

interface ReportPayload {
  testTitle: string
  testFile: string
  testStatus: string
  frontendErrors: FrontendError[]
  backendErrors: BackendError[]
  timestamp: string
}

function generateErrorsMd(payload: ReportPayload): string {
  const { testTitle, testFile, testStatus, frontendErrors, backendErrors, timestamp } = payload

  const statusLabel =
    testStatus === 'failed'
      ? 'FAILED'
      : frontendErrors.length > 0 || backendErrors.length > 0
        ? 'PASSED (with errors in console/backend)'
        : 'PASSED'

  const lines: string[] = [
    '# Test Error Report',
    '',
    `**Test:** ${testTitle}`,
    `**File:** ${testFile}`,
    `**Date:** ${timestamp}`,
    `**Status:** ${statusLabel}`,
    '',
  ]

  // Frontend errors section
  lines.push('## Frontend Errors', '')
  if (frontendErrors.length === 0) {
    lines.push('_No frontend errors._', '')
  } else {
    frontendErrors.forEach((err, i) => {
      lines.push(`### Error ${i + 1}`)
      lines.push(`- **Type:** ${err.type}`)
      lines.push(`- **Message:** ${err.message}`)
      if (err.stack) {
        lines.push('- **Stack:**')
        lines.push('  ```')
        err.stack.split('\n').forEach((l) => lines.push(`  ${l}`))
        lines.push('  ```')
      }
      lines.push(`- **Timestamp:** ${err.timestamp}`)
      lines.push('')
    })
  }

  // Backend errors section
  lines.push('## Backend Errors', '')
  if (backendErrors.length === 0) {
    lines.push('_No backend errors._', '')
  } else {
    backendErrors.forEach((err, i) => {
      lines.push(`### Error ${i + 1}`)
      lines.push(`- **Level:** ${err.level.toUpperCase()}`)
      lines.push(`- **Event:** ${err.event}`)
      if (err.filename) {
        lines.push(`- **File:** ${err.filename}:${err.lineno} (${err.func_name})`)
      }
      lines.push(`- **Timestamp:** ${err.timestamp}`)
      if (err.traceback) {
        lines.push('- **Traceback:**')
        lines.push('  ```')
        err.traceback.split('\n').forEach((l) => lines.push(`  ${l}`))
        lines.push('  ```')
      }
      lines.push('')
    })
  }

  // Agent instructions
  lines.push('## Agent Instructions', '')
  lines.push(
    'Read this file to understand the errors. Then find and fix the source files listed below.',
    '',
  )

  const backendFiles = [
    ...new Set(
      backendErrors
        .filter((e) => e.filename)
        .map((e) => `api/src/.../${e.filename}:${e.lineno}`),
    ),
  ]
  const tracebackFiles = backendErrors
    .filter((e) => e.traceback)
    .flatMap((e) =>
      [...(e.traceback ?? '').matchAll(/File "([^"]+)", line (\d+)/g)].map(
        (m) => `${m[1]}:${m[2]}`,
      ),
    )

  if (backendFiles.length > 0 || tracebackFiles.length > 0) {
    lines.push('### Backend files to investigate:')
    ;[...backendFiles, ...new Set(tracebackFiles)].forEach((f) => lines.push(`- \`${f}\``))
    lines.push('')
  }

  if (frontendErrors.some((e) => e.stack)) {
    lines.push('### Frontend: check stack traces above for component/file references.', '')
  }

  lines.push(`### Test file: \`${testFile}\``, '')

  return lines.join('\n')
}

function updateSummary(entry: {
  testTitle: string
  folderName: string
  testStatus: string
  frontendErrors: FrontendError[]
  backendErrors: BackendError[]
}): void {
  const summaryPath = path.join(REPORTS_DIR, 'summary.md')

  const fe = entry.frontendErrors.length
  const be = entry.backendErrors.length
  const status = entry.testStatus === 'failed' ? '❌ FAILED' : fe > 0 || be > 0 ? '⚠️ WARN' : '✅ PASSED'

  const newRow = `| ${status} | ${entry.testTitle} | ${fe} | ${be} | [report](tests/${entry.folderName}/errors.md) |`

  let existing = ''
  if (fs.existsSync(summaryPath)) {
    existing = fs.readFileSync(summaryPath, 'utf-8')
  } else {
    existing = [
      '# E2E Test Run Summary',
      '',
      '| Status | Test | Frontend Errors | Backend Errors | Report |',
      '|--------|------|-----------------|----------------|--------|',
      '',
    ].join('\n')
  }

  // Insert the new row before the last empty line
  const withRow = existing.trimEnd() + '\n' + newRow + '\n'
  fs.writeFileSync(summaryPath, withRow)
}

// ─── Cypress config ───────────────────────────────────────────────────────────

// Path to @vitejs/plugin-basic-ssl self-signed CA cert
// This cert is generated by Vite at startup and stored in the Vite cache dir
const VITE_SSL_CERT = path.resolve(
  __dirname,
  '../../../node_modules/.vite/apps/@ipr/magnet-admin/basic-ssl/_cert.pem',
)

const nxPreset = nxE2EPreset(__filename, {
  cypressDir: 'cypress',
  webServerCommands: {
    default: 'nx run magnet-admin:dev',
    production: 'nx run magnet-admin:preview',
  },
})

export default defineConfig({
  e2e: {
    ...nxPreset,
    // App is served at /admin/ — cy.visit('') lands on https://localhost:7000/admin/
    // cy.visit('#/route') → https://localhost:7000/admin/#/route
    baseUrl: 'https://localhost:7000/admin/',
    pageLoadTimeout: 90000,
    screenshotsFolder: path.join(REPORTS_DIR, 'screenshots'),
    // On macOS, Vite binds to ::1 (IPv6) while Electron resolves localhost to 127.0.0.1.
    // Cypress proxy uses this hosts map when routing requests → connects to Vite on ::1.
    hosts: { 'localhost': '::1' },

    setupNodeEvents(on, config) {
      // Pass the CA cert to Node.js so https requests in tasks trust it
      if (fs.existsSync(VITE_SSL_CERT)) {
        process.env.NODE_EXTRA_CA_CERTS = VITE_SSL_CERT
      }

      // Preserve Nx preset's own node events
      nxPreset.setupNodeEvents?.(on, config)

      // Fix for macOS: Vite binds to ::1 (IPv6) but Electron resolves localhost to 127.0.0.1 (IPv4).
      // Force Electron to use IPv6 for localhost and ignore the self-signed SSL cert.
      on('before:browser:launch', (_browser, launchOptions) => {
        launchOptions.args = launchOptions.args ?? []
        launchOptions.args.push('--ignore-certificate-errors')
        launchOptions.args.push('--host-resolver-rules=MAP localhost [::1]')
        return launchOptions
      })

      on('task', {
        resetBackendErrors() {
          return httpPost(`${BACKEND_URL}/api/test/errors/reset`).then(() => null)
        },

        getBackendErrors() {
          return httpGet(`${BACKEND_URL}/api/test/errors`)
        },

        saveTestReport(payload: ReportPayload) {
          const folderName = `${sanitizeName(payload.testTitle)}--${payload.timestamp.replace(/[:.]/g, '-')}`
          const testDir = path.join(REPORTS_DIR, 'tests', folderName)
          fs.mkdirSync(testDir, { recursive: true })

          // Raw logs (one JSON object per line)
          fs.writeFileSync(
            path.join(testDir, 'frontend.log'),
            payload.frontendErrors.map((e) => JSON.stringify(e)).join('\n'),
          )
          fs.writeFileSync(
            path.join(testDir, 'backend.log'),
            payload.backendErrors.map((e) => JSON.stringify(e)).join('\n'),
          )

          // Human + agent readable report
          fs.writeFileSync(path.join(testDir, 'errors.md'), generateErrorsMd(payload))

          // Update global summary
          updateSummary({
            testTitle: payload.testTitle,
            folderName,
            testStatus: payload.testStatus,
            frontendErrors: payload.frontendErrors,
            backendErrors: payload.backendErrors,
          })

          return null
        },
      })

      return config
    },
  },
})
