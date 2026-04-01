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

  function onMouseMove(e: MouseEvent) {
    if (!isResizing) return
    const delta = startX - e.clientX  // drawer is on the right, drag left = wider
    const newWidth = Math.min(maxWidth, Math.max(minWidth, startWidth + delta))
    width.value = newWidth
  }

  function onMouseUp() {
    if (!isResizing) return
    isResizing = false
    document.body.classList.remove('km-drawer-resizing')
    localStorage.setItem(storageKey, String(width.value))
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  function onResizeStart(e: MouseEvent) {
    e.preventDefault()
    startX = e.clientX
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

  return {
    width,
    drawerStyle,
    onResizeStart,
  }
}
