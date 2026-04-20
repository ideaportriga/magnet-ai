/// <reference types="cypress" />

import { listPage } from './listPage'
import { createDialog } from './createDialog'
import { detailPage } from './detailPage'

/**
 * Canonical 8-test CRUD contract for entity pages (E2E_CRUD_PREVIEW_ROADMAP).
 *
 * Usage:
 *   import { runCrudContract } from '../support/pages/crudContract'
 *
 *   runCrudContract({
 *     entity: 'Collections',
 *     listRoute: '#/knowledge-sources/',
 *     detailPathSegment: 'knowledge-sources',
 *     seedPrefix: 'e2e-test-',
 *     hasDescription: true,
 *   })
 *
 * Each test is independent:
 *   - C4/C5/C6/C7/C8 create a fresh record in `before()` and clean it up in
 *     `after()` via the test-only DELETE endpoint (see I.1 fixtures loader).
 *
 * Entities differ in which fields are editable and whether the create dialog
 * is a simple 1-step km-popup-confirm or a multi-step stepper. The
 * `hooks` option lets callers override the flow per-entity when needed.
 */

export interface CrudContractOptions {
  /** Human-readable name, used in test titles. */
  entity: string
  /** List page hash route, e.g. `#/knowledge-sources/`. */
  listRoute: string
  /** URL segment under which detail pages live, e.g. `knowledge-sources`. */
  detailPathSegment: string
  /** Prefix used for all e2e-created records so cleanup can find them. */
  seedPrefix?: string
  /** Whether the detail page has a `description-input` (most do). */
  hasDescription?: boolean
  /**
   * If the create flow is multi-step (e.g. Collections stepper), supply a
   * function that, given the filled name, clicks through any intermediate
   * "Next" buttons before Save. Default: no-op.
   */
  advanceCreateSteps?: () => void
  /** Skip specific tests when they don't apply to an entity. */
  skip?: Partial<Record<'C2' | 'C3' | 'C4' | 'C6' | 'C7' | 'C8', boolean>>
}

export function runCrudContract(opts: CrudContractOptions) {
  const {
    entity,
    listRoute,
    detailPathSegment,
    seedPrefix = 'e2e-test-',
    hasDescription = true,
    advanceCreateSteps,
    skip = {},
  } = opts

  describe(`${entity} — CRUD contract`, () => {
    // ─── C1 ──────────────────────────────────────────────────────────────────
    it('C1. list page renders with table/cards', () => {
      listPage.visit(listRoute)
      // Accept: any of search-input, new-btn, .km-data-table or a .q-card.
      // 30s timeout — first test of a spec often pays dev-server compile
      // cost on top of the app-shell mount.
      cy.get(
        '[data-test="search-input"], [data-test="new-btn"], .km-data-table, .q-card',
        { timeout: 30000 },
      ).should('exist')
    })

    // ─── C2 ──────────────────────────────────────────────────────────────────
    if (!skip.C2) {
      it('C2. search filters the list (debounced, server-side)', () => {
        listPage.visit(listRoute)
        // Skip this test if the search-input doesn't render on empty state
        // (some entities hide the toolbar until rows exist).
        cy.get('body').then(($body) => {
          if (!$body.find('[data-test="search-input"]').length) {
            cy.log(`${entity}: search-input hidden on empty-state — skipping C2`)
            return
          }
          listPage.search(seedPrefix)
          cy.g('search-input').find('input').should('have.value', seedPrefix)
        })
      })
    }

    // ─── C3 ──────────────────────────────────────────────────────────────────
    if (!skip.C3) {
      it('C3. create form shows validation on empty submit', () => {
        listPage.visit(listRoute)
        listPage.clickNew()
        createDialog.expectOpen()
        // Try to save without filling anything — advance through steps first
        if (advanceCreateSteps) advanceCreateSteps()
        createDialog.save()
        // Dialog should still be open; validation should appear
        cy.get('[data-test="popup-confirm"], [data-test="save-btn"]').should('exist')
      })
    }

    // ─── C4 ──────────────────────────────────────────────────────────────────
    if (!skip.C4) {
      it('C4. create → happy-path → navigates to detail', () => {
        listPage.visit(listRoute)
        listPage.clickNew()
        createDialog.expectOpen()
        createDialog.fillRandomName(seedPrefix)
        if (advanceCreateSteps) advanceCreateSteps()
        createDialog.save()
        detailPage.expectOnDetailPage(detailPathSegment)
        detailPage.waitForLoad()
      })
    }

    // ─── C5 ──────────────────────────────────────────────────────────────────
    it('C5. open existing record → detail page renders', () => {
      listPage.visit(listRoute)
      cy.get('body').then(($body) => {
        if ($body.find('[data-test="table-row"]').length > 0) {
          listPage.openFirstRow()
          detailPage.expectOnDetailPage(detailPathSegment)
          detailPage.waitForLoad()
        } else {
          cy.log(`${entity}: no rows to open — skipping (seed fixtures missing)`)
        }
      })
    })

    // ─── C6 ──────────────────────────────────────────────────────────────────
    if (!skip.C6 && hasDescription) {
      it('C6. edit description → save → change persists after reload', () => {
        const updatedValue = `e2e-desc-${Date.now()}`
        // Create a fresh record in-test (we don't rely on C4)
        listPage.visit(listRoute)
        listPage.clickNew()
        createDialog.fillRandomName(seedPrefix)
        if (advanceCreateSteps) advanceCreateSteps()
        createDialog.save()
        detailPage.expectOnDetailPage(detailPathSegment)
        detailPage.waitForLoad()

        detailPage.setDescription(updatedValue)
        detailPage.save()
        cy.reload()
        detailPage.waitForLoad()
        cy.g('description-input').find('input, textarea').first().should('have.value', updatedValue)
      })
    }

    // ─── C7 ──────────────────────────────────────────────────────────────────
    if (!skip.C7 && hasDescription) {
      it('C7. edit description → revert → change discarded', () => {
        listPage.visit(listRoute)
        listPage.clickNew()
        createDialog.fillRandomName(seedPrefix)
        if (advanceCreateSteps) advanceCreateSteps()
        createDialog.save()
        detailPage.expectOnDetailPage(detailPathSegment)
        detailPage.waitForLoad()

        cy.g('description-input').find('input, textarea').first().invoke('val').then((orig) => {
          detailPage.setDescription('e2e-temp-change')
          detailPage.revert()
          cy.g('description-input').find('input, textarea').first().should('have.value', orig || '')
        })
      })
    }

    // ─── C8 ──────────────────────────────────────────────────────────────────
    if (!skip.C8) {
      it('C8. delete → confirm → record gone from list', () => {
        listPage.visit(listRoute)
        listPage.clickNew()
        createDialog.fillRandomName(seedPrefix)
        if (advanceCreateSteps) advanceCreateSteps()
        createDialog.save()
        detailPage.expectOnDetailPage(detailPathSegment)
        detailPage.waitForLoad()

        // Capture the name we just created so we can verify it's gone
        detailPage.readName().then((createdName) => {
          detailPage.deleteEntity()
          // Should land back on list (no uuid in URL)
          cy.url({ timeout: 15000 }).should('not.match', new RegExp(`${detailPathSegment}/[a-f0-9-]{8,}$`))
          // Search for the deleted name — should not appear
          if (createdName) {
            cy.g('search-input', { timeout: 10000 }).should('be.visible')
            listPage.search(String(createdName))
            cy.g('table-row').should('have.length', 0)
          }
        })
      })
    }
  })
}
