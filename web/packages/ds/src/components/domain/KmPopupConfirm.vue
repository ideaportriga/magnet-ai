<script setup lang="ts">
/**
 * `<km-popup-confirm>` — drop-in replacement for the legacy PopupConfirm
 * dialog used across admin (delete confirmations, save+exit prompts, etc.).
 *
 * Public API preserved 1:1:
 *   visible (v-model:visible), title, notification, notificationIcon,
 *   confirmButtonLabel, confirmButtonLabel2, confirmButtonType2,
 *   cancelButtonLabel, loading
 *
 * Emits: update:visible, cancel, confirm, confirm2.
 *
 * Internally renders `<DsAlertDialog>` (Reka's AlertDialog primitive) for
 * the simple single-confirm case. When `confirmButtonLabel2` is provided we
 * fall through to a DsDialog-equivalent custom shell because AlertDialog
 * caps at one confirm action — this preserves behaviour for save / discard
 * / cancel triple-buttoned legacy flows.
 */

import { computed, useId } from 'vue'
import DsAlertDialog from '../primitives/Dialog/DsAlertDialog.vue'
import DsDialog from '../primitives/Dialog/DsDialog.vue'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmInnerLoading from './KmInnerLoading.vue'
import KmNotificationText from './KmNotificationText.vue'

const props = withDefaults(
  defineProps<{
    loading?: boolean
    notification?: string
    notificationIcon?: string
    title?: string
    confirmButtonLabel?: string
    confirmButtonLabel2?: string
    confirmButtonType2?: 'default' | 'secondary'
    cancelButtonLabel?: string
    visible?: boolean
  }>(),
  {
    loading: false,
    notification: '',
    notificationIcon: '',
    title: '',
    confirmButtonLabel: 'Confirm',
    confirmButtonLabel2: '',
    confirmButtonType2: 'default',
    cancelButtonLabel: 'Cancel',
    visible: false,
  },
)

const emit = defineEmits<{
  'update:visible': [value: boolean]
  cancel: []
  confirm: []
  confirm2: []
}>()

const open = computed({
  get: () => props.visible,
  set: (next) => emit('update:visible', next),
})

/** Three-button mode (Save / Don't save / Cancel) needs a DsDialog shell. */
const hasSecondAction = computed(() => Boolean(props.confirmButtonLabel2))

/** Per-instance id so several popups mounted simultaneously don't share
 *  the same `<linearGradient>` id (the second one would silently fail). */
const gradientId = `km-popup-confirm-grad-${useId()}`

function cancel() {
  emit('cancel')
  open.value = false
}
function confirm() {
  emit('confirm')
  open.value = false
}
function confirm2() {
  // "Don't save" / discard branch — close eagerly so the popup never lingers
  // after the user chose to drop their changes (parent's `@confirm2` handler
  // typically navigates away, but the close was missing here).
  emit('confirm2')
  open.value = false
}
</script>

<template>
  <!-- Two-button (Confirm / Cancel) → AlertDialog. -->
  <DsAlertDialog
    v-if="!hasSecondAction"
    v-model:open="open"
    :title="title"
    :confirm-label="confirmButtonLabel"
    :cancel-label="cancelButtonLabel"
    data-test="km-popup-confirm"
    @confirm="confirm"
    @cancel="cancel"
  >
    <div class="km-popup-confirm__body stack" data-gap="md">
      <div v-if="notificationIcon" class="cluster" data-justify="center">
        <KmGlyph :name="notificationIcon" size="32px" />
      </div>
      <KmNotificationText v-if="notification" :notification="notification" />
      <slot />
      <KmInnerLoading :showing="loading" />
    </div>
  </DsAlertDialog>

  <!-- Three-button (e.g. Save / Don't save / Cancel) → DsDialog shell.
       `md` (500px) instead of `sm` so the three footer buttons fit on a
       single row even at the longest English labels ("Don't save changes"
       + "Save changes" + "Cancel"). -->
  <DsDialog
    v-else
    v-model:open="open"
    size="md"
    :dismissible="false"
    class="km-popup-confirm"
    data-test="km-popup-confirm"
    @update:open="(v) => v || cancel()"
  >
    <template #title>{{ title }}</template>

    <div class="km-popup-confirm__body stack" data-gap="md">
      <div v-if="notificationIcon" class="cluster" data-justify="center">
        <!-- Inline SVG warning glyph filled by a real `<linearGradient>` —
             reliable across browsers, unlike `background-clip: text` over a
             FontAwesome `::before`. The unique gradient id avoids ID
             collisions if multiple popups mount at once. -->
        <svg
          class="km-popup-confirm__icon"
          width="44"
          height="44"
          viewBox="0 0 48 48"
          aria-hidden="true"
        >
          <defs>
            <linearGradient
              :id="gradientId"
              x1="0"
              y1="0"
              x2="1"
              y2="1"
            >
              <stop offset="0%" stop-color="#5541d7" />
              <stop offset="100%" stop-color="#e30052" />
            </linearGradient>
          </defs>
          <path
            d="M24 6 L43 38 a3 3 0 0 1 -2.6 4.5 H7.6 a3 3 0 0 1 -2.6 -4.5 Z"
            :fill="`url(#${gradientId})`"
          />
          <rect x="22" y="18" width="4" height="12" rx="2" fill="var(--ds-color-static-white)" />
          <circle cx="24" cy="34" r="2" fill="var(--ds-color-static-white)" />
        </svg>
      </div>
      <KmNotificationText v-if="notification" :notification="notification" />
      <slot />
      <KmInnerLoading :showing="loading" />
    </div>

    <template #footer>
      <KmBtn
        flat
        class="km-popup-confirm__cancel"
        :label="cancelButtonLabel"
        tone="brand"
        :data-test="`popup-confirm-cancel-${cancelButtonLabel}`"
        @click="cancel"
      />
      <!-- "Don't save" follows Cancel's flat-link style; the only visual
           weight in the footer belongs to the primary "Save" action. -->
      <KmBtn
        flat
        :label="confirmButtonLabel2"
        tone="brand"
        :data-test="`popup-confirm-secondary-${confirmButtonLabel2}`"
        @click="confirm2"
      />
      <KmBtn
        :label="confirmButtonLabel"
        :data-test="`popup-confirm-${confirmButtonLabel}`"
        @click="confirm"
      />
    </template>
  </DsDialog>
</template>

<style>
.km-popup-confirm__body {
  position: relative;
  min-block-size: 4rem;
}

/* Push Cancel to the left edge of the footer; "Don't save" + "Save"
 * cluster against the right edge. The DsDialog footer is a flex row with
 * `justify-content: flex-end`, so a single `margin-inline-end: auto` on
 * the first child is enough — no extra wrapper. */
.km-popup-confirm .km-popup-confirm__cancel {
  margin-inline-end: auto;
}
/* Keep the three footer buttons on a single row even when the dialog is
 * close to its min-width. Buttons handle their own ellipsis if a label
 * really gets too long; wrapping the row would look worse than truncation. */
.km-popup-confirm .ds-dialog__footer {
  flex-wrap: nowrap;
}

.km-popup-confirm__icon {
  display: block;
  flex: none;
}
</style>
