/**
 * Persistent, draggable drawer width composable. Mirrors the legacy
 * `@ui-comp/composables/useDrawerResize` 1:1 — width is stored in
 * localStorage and clamped between `minWidth`/`maxWidth`.
 */

import { computed, onUnmounted, ref } from 'vue'

export interface UseDrawerResizeOptions {
  storageKey: string
  defaultWidth?: number
  minWidth?: number
  maxWidth?: number
}

export function useDrawerResize(options: UseDrawerResizeOptions) {
  const {
    storageKey,
    defaultWidth = 500,
    minWidth = 320,
    maxWidth = 900,
  } = options

  const savedWidth = typeof localStorage !== 'undefined' ? localStorage.getItem(storageKey) : null
  const width = ref<number>(
    savedWidth ? Math.min(maxWidth, Math.max(minWidth, Number.parseInt(savedWidth, 10))) : defaultWidth,
  )

  const drawerStyle = computed(() => ({
    width: `${width.value}px`,
    minWidth: `${width.value}px`,
    maxWidth: `${width.value}px`,
  }))

  let startX = 0
  let startWidth = 0
  let isResizing = false

  function onMouseMove(event: MouseEvent) {
    if (!isResizing) return
    const delta = startX - event.clientX
    width.value = Math.min(maxWidth, Math.max(minWidth, startWidth + delta))
  }

  function onMouseUp() {
    if (!isResizing) return
    isResizing = false
    document.body.classList.remove('km-drawer-resizing')
    if (typeof localStorage !== 'undefined') localStorage.setItem(storageKey, String(width.value))
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  function onResizeStart(event: MouseEvent) {
    event.preventDefault()
    startX = event.clientX
    startWidth = width.value
    isResizing = true
    document.body.classList.add('km-drawer-resizing')
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }

  onUnmounted(() => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.classList.remove('km-drawer-resizing')
  })

  return { width, drawerStyle, onResizeStart }
}
