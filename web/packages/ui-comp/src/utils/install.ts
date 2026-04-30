/**
 * `@ui-comp` Vue plugin install — Phase 4d redesign.
 *
 * Before this PR `@ui-comp` shipped its own 50 base/* SFC files and used
 * `import.meta.glob` to register them globally as `<km-*>`. With Phase 4d
 * the `Km*` family is owned by `@ds`; `@ui-comp` becomes a thin shim:
 *
 *   1. registers every export from `@ds/components/domain` (`KmBtn`,
 *      `KmInput`, …) under both PascalCase and kebab-case names, so legacy
 *      `<km-btn>` markup keeps working,
 *   2. registers the 14 shared non-base components (`<agent-message>`,
 *      `<auth-login-page>`, `<retrieval-prompt>`, `<search-feedback>`,
 *      `<user-menu>`, …) with explicit imports.
 *
 * The result is a single, statically analysable list of registrations —
 * no `import.meta.glob`, no implicit naming conventions to remember.
 */

import type { App, Component } from 'vue'
import * as kmComponents from '@ds/components/domain'
import {
  DsContextMenu,
  DsContextMenuTrigger,
  DsContextMenuPortal,
  DsContextMenuContent,
  DsContextMenuGroup,
  DsContextMenuItem,
  DsContextMenuCheckboxItem,
  DsContextMenuRadioGroup,
  DsContextMenuRadioItem,
  DsContextMenuLabel,
  DsContextMenuSeparator,
  DsContextMenuShortcut,
  DsContextMenuSub,
  DsContextMenuSubTrigger,
  DsContextMenuSubContent,
  DsDropdownMenuRoot,
  DsDropdownMenuTrigger,
  DsDropdownMenuPortal,
  DsDropdownMenuContent,
  DsDropdownMenuGroup,
  DsDropdownMenuItem,
  DsDropdownMenuCheckboxItem,
  DsDropdownMenuRadioGroup,
  DsDropdownMenuRadioItem,
  DsDropdownMenuLabel,
  DsDropdownMenuSeparator,
  DsDropdownMenuShortcut,
  DsDropdownMenuSub,
  DsDropdownMenuSubTrigger,
  DsDropdownMenuSubContent,
} from '@ds/primitives'

import AgentMessage from '../components/Agent/Message.vue'
import AgentConfirmation from '../components/Agent/Confirmation.vue'

import AuthLoginPage from '../components/auth/AuthLoginPage.vue'
import AuthSignupPage from '../components/auth/AuthSignupPage.vue'
import AuthForgotPassword from '../components/auth/AuthForgotPassword.vue'

import RetrievalPrompt from '../components/Retrieval/Prompt.vue'
import RetrievalAnswer from '../components/Retrieval/Answer.vue'

import SearchPrompt from '../components/Search/Prompt.vue'
import SearchAnswer from '../components/Search/Answer.vue'
import SearchFeedback from '../components/Search/Feedback.vue'
import SearchFeedbackConfirm from '../components/Search/FeedbackConfirm.vue'

import UserMenu from '../components/user/UserMenu.vue'
import UserProfilePage from '../components/user/UserProfilePage.vue'
import UserSecurityPage from '../components/user/UserSecurityPage.vue'

/** PascalCase → kebab-case (KmBtn → km-btn, KmDataTable → km-data-table). */
function toKebab(name: string): string {
  return name.replace(/([A-Z])/g, (_, c, index) => (index === 0 ? c.toLowerCase() : `-${c.toLowerCase()}`))
}

/**
 * `Ds*` menu primitives (ContextMenu + DropdownMenu families) registered
 * globally so that admin/panel templates can use `<ds-dropdown-menu-root>`
 * etc. without per-file imports — the same ergonomics as `<km-*>`.
 */
const dsMenuComponents: Record<string, Component> = {
  DsContextMenu,
  DsContextMenuTrigger,
  DsContextMenuPortal,
  DsContextMenuContent,
  DsContextMenuGroup,
  DsContextMenuItem,
  DsContextMenuCheckboxItem,
  DsContextMenuRadioGroup,
  DsContextMenuRadioItem,
  DsContextMenuLabel,
  DsContextMenuSeparator,
  DsContextMenuShortcut,
  DsContextMenuSub,
  DsContextMenuSubTrigger,
  DsContextMenuSubContent,
  DsDropdownMenuRoot,
  DsDropdownMenuTrigger,
  DsDropdownMenuPortal,
  DsDropdownMenuContent,
  DsDropdownMenuGroup,
  DsDropdownMenuItem,
  DsDropdownMenuCheckboxItem,
  DsDropdownMenuRadioGroup,
  DsDropdownMenuRadioItem,
  DsDropdownMenuLabel,
  DsDropdownMenuSeparator,
  DsDropdownMenuShortcut,
  DsDropdownMenuSub,
  DsDropdownMenuSubTrigger,
  DsDropdownMenuSubContent,
}

const sharedComponents: Record<string, Component> = {
  AgentMessage,
  AgentConfirmation,
  AuthLoginPage,
  AuthSignupPage,
  AuthForgotPassword,
  RetrievalPrompt,
  RetrievalAnswer,
  SearchPrompt,
  SearchAnswer,
  SearchFeedback,
  SearchFeedbackConfirm,
  UserMenu,
  UserProfilePage,
  UserSecurityPage,
}

export function registerComponents(app: App): void {
  // Km* from @ds — registered under PascalCase. Vue 3 resolves `<KmBtn>`
  // and `<km-btn>` from the same registration, so legacy templates keep
  // working without re-registering both casings.
  for (const [name, component] of Object.entries(kmComponents)) {
    if (component) app.component(name, component as Component)
  }

  // Ds* menu primitives — same dual-casing scheme as the shared block,
  // because admin templates use kebab-case (`<ds-dropdown-menu-item>`).
  for (const [name, component] of Object.entries(dsMenuComponents)) {
    app.component(name, component)
    app.component(toKebab(name), component)
  }

  // Shared non-base components — registered under both PascalCase and
  // kebab-case to match the legacy `import.meta.glob` behaviour exactly.
  for (const [name, component] of Object.entries(sharedComponents)) {
    app.component(name, component)
    app.component(toKebab(name), component)
  }
}

export default {
  install(app: App): void {
    registerComponents(app)
  },
}
