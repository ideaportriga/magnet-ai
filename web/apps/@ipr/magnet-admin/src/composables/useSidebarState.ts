import { ref, computed, onMounted, onUnmounted } from 'vue'

type SidebarMode = 'expanded' | 'collapsed'

const STORAGE_KEY = 'sidebar-mode'
const SECTIONS_STORAGE_KEY = 'sidebar-sections'
const EXPANDED_WIDTH = 220
const COLLAPSED_WIDTH = 56
const BREAKPOINT = 1350

// Shared state across components (singleton)
const mode = ref<SidebarMode>(
  (localStorage.getItem(STORAGE_KEY) as SidebarMode) || 'expanded'
)

const sectionState = ref<Record<string, boolean>>(
  JSON.parse(localStorage.getItem(SECTIONS_STORAGE_KEY) || '{}')
)

export function useSidebarState() {
  function toggle() {
    mode.value = mode.value === 'expanded' ? 'collapsed' : 'expanded'
    localStorage.setItem(STORAGE_KEY, mode.value)
  }

  function toggleSection(key: string) {
    sectionState.value = {
      ...sectionState.value,
      [key]: !sectionState.value[key],
    }
    localStorage.setItem(SECTIONS_STORAGE_KEY, JSON.stringify(sectionState.value))
  }

  function isSectionCollapsed(key: string): boolean {
    return !!sectionState.value[key]
  }

  const sidebarWidth = computed(() =>
    mode.value === 'expanded' ? EXPANDED_WIDTH : COLLAPSED_WIDTH
  )

  const isCollapsed = computed(() => mode.value === 'collapsed')

  // Auto-collapse on small screens
  function handleResize() {
    if (window.innerWidth < BREAKPOINT && mode.value === 'expanded') {
      mode.value = 'collapsed'
      localStorage.setItem(STORAGE_KEY, mode.value)
    }
  }

  // Keyboard shortcut: Ctrl+B to toggle
  function handleKeydown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
      e.preventDefault()
      toggle()
    }
  }

  onMounted(() => {
    window.addEventListener('resize', handleResize)
    window.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('keydown', handleKeydown)
  })

  return {
    mode,
    toggle,
    sidebarWidth,
    isCollapsed,
    sectionState,
    toggleSection,
    isSectionCollapsed,
  }
}
