<script setup lang="ts">
/**
 * SidebarProvider — wraps the app shell, owns the sidebar's open/collapsed
 * state, exposes context via {@link useSidebar}, persists the desktop state in
 * a cookie, and binds the Cmd/Ctrl+B keyboard shortcut.
 */

import type { Ref } from 'vue'
import { defaultDocument, useEventListener, useMediaQuery, useVModel } from '@vueuse/core'
import { TooltipProvider } from 'reka-ui'
import { computed, ref } from 'vue'
import {
  provideSidebarContext,
  SIDEBAR_COOKIE_MAX_AGE,
  SIDEBAR_COOKIE_NAME,
  SIDEBAR_KEYBOARD_SHORTCUT,
  SIDEBAR_WIDTH,
  SIDEBAR_WIDTH_ICON,
} from './utils'

const props = withDefaults(
  defineProps<{
    defaultOpen?: boolean
    open?: boolean
  }>(),
  {
    defaultOpen: !defaultDocument?.cookie.includes(`${SIDEBAR_COOKIE_NAME}=false`),
    open: undefined,
  },
)

const emits = defineEmits<{
  'update:open': [open: boolean]
}>()

const isMobile = useMediaQuery('(max-width: 768px)')
const openMobile = ref(false)

const open = useVModel(props, 'open', emits, {
  defaultValue: props.defaultOpen ?? false,
  passive: (props.open === undefined) as false,
}) as Ref<boolean>

function setOpen(value: boolean) {
  open.value = value
  document.cookie = `${SIDEBAR_COOKIE_NAME}=${open.value}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`
}

function setOpenMobile(value: boolean) {
  openMobile.value = value
}

function toggleSidebar() {
  return isMobile.value ? setOpenMobile(!openMobile.value) : setOpen(!open.value)
}

useEventListener('keydown', (event: KeyboardEvent) => {
  if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    toggleSidebar()
  }
})

const state = computed(() => (open.value ? 'expanded' : 'collapsed'))

provideSidebarContext({
  state,
  open,
  setOpen,
  isMobile,
  openMobile,
  setOpenMobile,
  toggleSidebar,
})
</script>

<template>
  <TooltipProvider :delay-duration="0">
    <div
      class="ds-sidebar-wrapper"
      data-test="ds-sidebar-wrapper"
      :style="{
        '--ds-sidebar-width': SIDEBAR_WIDTH,
        '--ds-sidebar-width-icon': SIDEBAR_WIDTH_ICON,
      }"
    >
      <slot />
    </div>
  </TooltipProvider>
</template>

<style>
.ds-sidebar-wrapper {
  display: flex;
  min-block-size: 100svb;
  inline-size: 100%;
}
.ds-sidebar-wrapper:has([data-variant='inset']) {
  background: var(--ds-color-light);
}
</style>
