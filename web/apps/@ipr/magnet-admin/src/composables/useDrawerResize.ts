import { ref, computed, onUnmounted } from 'vue'

interface UseDrawerResizeOptions {
  storageKey: string
  defaultWidth?: number  // default: 500
  minWidth?: number      // default: 320
  maxWidth?: number      // default: 900
}

export function useDrawerResize(options: UseDrawerResizeOptions) {
  const {
    storageKey,
    defaultWidth = 500,
    minWidth = 320,
    maxWidth = 900,
  } = options

  // Load persisted width
  const savedWidth = localStorage.getItem(storageKey)
  const width = ref<number>(
    savedWidth ? Math.min(maxWidth, Math.max(minWidth, parseInt(savedWidth, 10))) : defaultWidth
  )

  const drawerStyle = computed(() => ({
    width: `${width.value}px`,
    minWidth: `${width.value}px`,
    maxWidth: `${width.value}px`,
  }))

  let startX = 0
  let startWidth = 0
  let isResizing = false

  // §B.7 — pointer events + setPointerCapture so we always get a pointerup,
  // even when the user releases the mouse outside the viewport. The old
  // mousemove/mouseup pair leaked handlers any time that happened.

  function onPointerMove(e: PointerEvent) {
    if (!isResizing) return
    const delta = startX - e.clientX  // drawer is on the right, drag left = wider
    width.value = Math.min(maxWidth, Math.max(minWidth, startWidth + delta))
  }

  function finishResize() {
    if (!isResizing) return
    isResizing = false
    document.body.classList.remove('km-drawer-resizing')
    localStorage.setItem(storageKey, String(width.value))
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerup', finishResize)
    document.removeEventListener('pointercancel', finishResize)
  }

  function onResizeStart(e: PointerEvent | MouseEvent) {
    e.preventDefault()
    startX = (e as PointerEvent).clientX ?? (e as MouseEvent).clientX
    startWidth = width.value
    isResizing = true
    document.body.classList.add('km-drawer-resizing')

    // Capture the pointer so any window-exit still reports up/cancel to us.
    const pointer = e as PointerEvent
    if (typeof pointer.pointerId === 'number' && e.target instanceof Element) {
      try {
        (e.target as Element).setPointerCapture?.(pointer.pointerId)
      } catch {
        // setPointerCapture may fail on non-interactive targets; safe to ignore.
      }
    }

    document.addEventListener('pointermove', onPointerMove)
    document.addEventListener('pointerup', finishResize)
    document.addEventListener('pointercancel', finishResize)
  }

  onUnmounted(() => {
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerup', finishResize)
    document.removeEventListener('pointercancel', finishResize)
    document.body.classList.remove('km-drawer-resizing')
  })

  return {
    width,
    drawerStyle,
    onResizeStart,
  }
}
