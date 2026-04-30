/**
 * `@ui-comp` — public entry point.
 *
 * Phase 4d: this package is now a thin bridge over `@ds`. The default
 * export is the Vue plugin (`app.use(uiComps)`); the named re-exports of
 * `Km*` come from `@ds/components/domain` so existing `import { KmBtn }
 * from '@ui'` style imports continue to work.
 *
 * The 14 shared non-base components (Agent / auth / Retrieval / Search /
 * user) are exposed as named exports too, so apps can import them without
 * relying on the global plugin install.
 */

import install from './utils/install'

// Default export — Vue plugin install.
export default install

// Re-export every Km* from the design system. Exists so legacy named
// imports (`import { KmBtn } from '@ui'`) keep resolving.
export * from '@ds/components/domain'

// Legacy named exports — older admin code imports these without the `Km`
// prefix (`import { ChipCopy } from '@ui'`). Keep them aliased so the
// codebase doesn't need a single-PR rename.
export {
  KmAvatar as Avatar,
  KmBackground as Background,
  KmBadge as Badge,
  KmBtn as Btn,
  KmBtnExpandDown as BtnExpandDown,
  KmBtnLoader as BtnLoader,
  KmCard as Card,
  KmCheckbox as Checkbox,
  KmChip as Chip,
  KmChipCopy as ChipCopy,
  KmChipsInput as ChipsInput,
  KmCodemirror as Codemirror,
  KmConfirmAction as ConfirmAction,
  KmDataTable as DataTable,
  KmDate as Date,
  KmDrawer as Drawer,
  KmDrawerLayout as DrawerLayout,
  KmEmptyState as EmptyState,
  KmErrorDialog as ErrorDialog,
  KmFilePicker as FilePicker,
  KmFilterBar as FilterBar,
  KmIcon as Icon,
  KmIconBtn as IconBtn,
  KmIconPicker as IconPicker,
  KmImage as Image,
  KmInnerLoading as InnerLoading,
  KmInput as Input,
  KmInputFlat as InputFlat,
  KmInputListAdd as InputListAdd,
  KmJsonEditor as JsonEditor,
  KmLoader as Loader,
  KmLocaleSwitcher as LocaleSwitcher,
  KmMarkdown as Markdown,
  KmNavSection as NavSection,
  KmNotificationText as NotificationText,
  KmPicker as Picker,
  KmPopupConfirm as PopupConfirm,
  KmRange as Range,
  KmScore as Score,
  KmSection as Section,
  KmSelect as Select,
  KmSelectFlat as SelectFlat,
  KmSeparator as Separator,
  KmSlider as Slider,
  KmSliderCard as SliderCard,
  KmStepper as Stepper,
  KmSwitch as Switch,
  KmTabs as Tabs,
  KmToggle as Toggle,
  KmTooltip as Tooltip,
} from '@ds/components/domain'

// Shared non-base components (admin + panel use these via global
// registration; some admin code-gen helpers — e.g. `evaluation_set_records.js`
// — also import them directly).
export { default as AgentMessage } from './components/Agent/Message.vue'
export { default as AgentConfirmation } from './components/Agent/Confirmation.vue'
export { default as AuthLoginPage } from './components/auth/AuthLoginPage.vue'
export { default as AuthSignupPage } from './components/auth/AuthSignupPage.vue'
export { default as AuthForgotPassword } from './components/auth/AuthForgotPassword.vue'
export { default as RetrievalPrompt } from './components/Retrieval/Prompt.vue'
export { default as RetrievalAnswer } from './components/Retrieval/Answer.vue'
export { default as SearchPrompt } from './components/Search/Prompt.vue'
export { default as SearchAnswer } from './components/Search/Answer.vue'
export { default as SearchFeedback } from './components/Search/Feedback.vue'
export { default as SearchFeedbackConfirm } from './components/Search/FeedbackConfirm.vue'
export { default as UserMenu } from './components/user/UserMenu.vue'
export { default as UserProfilePage } from './components/user/UserProfilePage.vue'
export { default as UserSecurityPage } from './components/user/UserSecurityPage.vue'
