/**
 * @ds domain components — `Km*` family.
 *
 * Each component preserves the public API of its `@ui-comp` legacy twin so
 * the codemod step in Phase 4 can swap one for the other without touching
 * call sites. Internally they compose from `@ds` primitives, tokens, and
 * CUBE composition utilities — zero Quasar.
 */

// ─── Foundation (Wave 1) ─────────────────────────────────────────────────
import KmIcon from './KmIcon.vue'
import KmGlyph from './KmGlyph.vue'
import KmSeparator from './KmSeparator.vue'
import KmTooltip from './KmTooltip.vue'
import KmAvatar from './KmAvatar.vue'
import KmCard from './KmCard.vue'
import KmEmptyState from './KmEmptyState.vue'
import KmLoader from './KmLoader.vue'
import KmInnerLoading from './KmInnerLoading.vue'
import KmBadge from './KmBadge.vue'
import KmChip from './KmChip.vue'
import KmNotificationText from './KmNotificationText.vue'

// ─── Buttons (Wave 2) ────────────────────────────────────────────────────
import KmBtn from './KmBtn.vue'
import KmIconBtn from './KmIconBtn.vue'
import KmBtnLoader from './KmBtnLoader.vue'
import KmBtnExpandDown from './KmBtnExpandDown.vue'
import KmNavBtn from './KmNavBtn.vue'

// ─── Simple forms (Wave 3) ───────────────────────────────────────────────
import KmCheckbox from './KmCheckbox.vue'
import KmSwitch from './KmSwitch.vue'
import KmToggle from './KmToggle.vue'
import KmSlider from './KmSlider.vue'

// ─── Overlays (Wave 4) ───────────────────────────────────────────────────
import KmPopupConfirm from './KmPopupConfirm.vue'
import KmConfirmAction from './KmConfirmAction.vue'
import KmErrorDialog from './KmErrorDialog.vue'

// ─── Complex forms (Wave 5) ──────────────────────────────────────────────
import KmInput from './KmInput.vue'
import KmInputFlat from './KmInputFlat.vue'
import KmSelect from './KmSelect.vue'
import KmSelectFlat from './KmSelectFlat.vue'
import KmDropdownSelect from './KmDropdownSelect.vue'
import KmTabs from './KmTabs.vue'
import KmTab from './KmTab.vue'
import KmFilePicker from './KmFilePicker.vue'
import KmChipsInput from './KmChipsInput.vue'

// ─── Layout / nav (Wave 6) ───────────────────────────────────────────────
import KmSection from './KmSection.vue'
import KmBackground from './KmBackground.vue'
import KmNavSection from './KmNavSection.vue'
import KmDrawer from './KmDrawer.vue'
import KmDrawerLayout from './KmDrawerLayout.vue'
import KmDrawerResizeHandle from './KmDrawerResizeHandle.vue'
import KmStepper from './KmStepper.vue'
import KmFilterBar from './KmFilterBar.vue'

// ─── Misc (Wave 7) ───────────────────────────────────────────────────────
import KmImage from './KmImage.vue'
import KmScore from './KmScore.vue'
import KmSliderCard from './KmSliderCard.vue'
import KmChipCopy from './KmChipCopy.vue'
import KmLocaleSwitcher from './KmLocaleSwitcher.vue'

// ─── Phase 3.5: editors / pickers / dates / data ─────────────────────────
import KmInputListAdd from './KmInputListAdd.vue'
import KmMarkdown from './KmMarkdown.vue'
import KmJsonEditor from './KmJsonEditor.vue'
import KmCodemirror from './KmCodemirror.vue'
import KmPicker from './KmPicker.vue'
import KmIconPicker from './KmIconPicker.vue'
import KmDate from './KmDate.vue'
import KmRange from './KmRange.vue'
import KmDataTable from './KmDataTable.vue'

// ─── Reka-backed Km* (rewritten from Quasar widgets) ─────────────────────
import KmMenu from './KmMenu.vue'
import KmPopover from './KmPopover.vue'
import KmDialog from './KmDialog.vue'
import KmBanner from './KmBanner.vue'
import KmLinearProgress from './KmLinearProgress.vue'
import KmScrollArea from './KmScrollArea.vue'
import KmRadio from './KmRadio.vue'
import KmSlideTransition from './KmSlideTransition.vue'
import KmExpansionItem from './KmExpansionItem.vue'
import KmTable from './KmTable.vue'
import KmTabPanels from './KmTabPanels.vue'
import KmTabPanel from './KmTabPanel.vue'
import KmStep from './KmStep.vue'
import KmTimeline from './KmTimeline.vue'
import KmTimelineEntry from './KmTimelineEntry.vue'
import KmTree from './KmTree.vue'
import KmBtnDropdown from './KmBtnDropdown.vue'
import KmBtnToggle from './KmBtnToggle.vue'
import KmOptionGroup from './KmOptionGroup.vue'
import KmPopupEdit from './KmPopupEdit.vue'
import KmBreadcrumbNav from './KmBreadcrumbNav.vue'

export {
  // Foundation
  KmIcon,
  KmGlyph,
  KmSeparator,
  KmTooltip,
  KmAvatar,
  KmCard,
  KmEmptyState,
  KmLoader,
  KmInnerLoading,
  KmBadge,
  KmChip,
  KmNotificationText,
  // Buttons
  KmBtn,
  KmIconBtn,
  KmBtnLoader,
  KmBtnExpandDown,
  KmNavBtn,
  // Simple forms
  KmCheckbox,
  KmSwitch,
  KmToggle,
  KmSlider,
  // Overlays
  KmPopupConfirm,
  KmConfirmAction,
  KmErrorDialog,
  // Complex forms
  KmInput,
  KmInputFlat,
  KmSelect,
  KmSelectFlat,
  KmDropdownSelect,
  KmTabs,
  KmTab,
  KmFilePicker,
  KmChipsInput,
  // Layout / nav
  KmSection,
  KmBackground,
  KmNavSection,
  KmDrawer,
  KmDrawerLayout,
  KmDrawerResizeHandle,
  KmStepper,
  KmFilterBar,
  // Misc
  KmImage,
  KmScore,
  KmSliderCard,
  KmChipCopy,
  KmLocaleSwitcher,
  // Phase 3.5
  KmInputListAdd,
  KmMarkdown,
  KmJsonEditor,
  KmCodemirror,
  KmPicker,
  KmIconPicker,
  KmDate,
  KmRange,
  KmDataTable,
  // Reka-backed widgets
  KmMenu,
  KmPopover,
  KmDialog,
  KmBanner,
  KmLinearProgress,
  KmScrollArea,
  KmRadio,
  KmSlideTransition,
  KmExpansionItem,
  KmTable,
  KmTabPanels,
  KmTabPanel,
  KmStep,
  KmTimeline,
  KmTimelineEntry,
  KmTree,
  KmBtnDropdown,
  KmBtnToggle,
  KmOptionGroup,
  KmPopupEdit,
  // Navigation
  KmBreadcrumbNav,
}
