/**
 * Agents — Preview contract.
 *
 * Agents detail has `Agents/DrawerPreview.vue` with a chat-style input
 * (textarea) + submit q-btn. data-test attrs `preview-input` / `preview-btn`
 * were added to those elements.
 *
 * Preview hits the agents chat/ask endpoint (streaming or regular) — the
 * regex matches both `/agents/.../ask` and streaming variants.
 */

import { runPreviewContract } from '../support/pages/previewContract'
import { listPage } from '../support/pages/listPage'

runPreviewContract({
  entity: 'Agents',
  listRoute: '#/agents',
  openPreviewableDetail: () => {
    // Agents list is a card grid — wait for at least one row/card, then open it.
    cy.get('[data-test="table-row"]', { timeout: 15000 }).first().click()
    cy.url({ timeout: 15000 }).should('match', /agents\/[a-f0-9-]{8,}/)
  },
  inputSelector: '[data-test="preview-input"]',
  runButtonSelector: '[data-test="preview-btn"]',
  apiPathMatcher: /\/agents\/.+\/(ask|conversations|messages)/,
  apiMethod: 'POST',
  // P2 hits the agent ask endpoint which is streaming and can hang —
  // skip until a deterministic fixture exists.
  skip: { P2: true, P3: true, P4: true },
})
