<template>
  <div class="km-layout bg-light full-height overflow-hidden">
    <header class="km-header">
      <div class="cluster bg-white text-black bb-border km-header__bar" data-wrap="no" data-test="header">
        <div class="cluster flex-none full-height br-border km-sidebar-header" data-wrap="no" data-justify="center" :style="{ width: sidebarWidth + &quot;px&quot; }">
          <div v-if="!isCollapsed" class="cluster cursor-pointer full-height" data-wrap="no" data-gap="sm" @click="navigate(&quot;/&quot;)">
            <km-icon :name="&quot;magnet&quot;" width="20" height="23" />
            <div class="relative-position">
              <div class="km-heading-6 logo-text">Magnet AI</div>
              <div class="absolute km-header__env-tag">
                <div class="logo-text">{{ environment }}</div>
              </div>
            </div>
          </div>
          <div v-else class="cluster cursor-pointer full-height" data-wrap="no" data-justify="center" @click="navigate(&quot;/&quot;)">
            <km-icon :name="&quot;magnet&quot;" width="20" height="23" />
          </div>
        </div>
        <km-glyph class="flex-none cursor-pointer ml-md km-sidebar-toggle" name="columns" size="16px" tone="subtle" @click.stop="toggleSidebar" />
        <div v-if="showPageLabel || showBackButton" class="cluster flex-none mx-md" data-wrap="no" data-gap="sm">
          <span class="km-body km-breadcrumb-item" :class="showBackButton ? &quot;text-primary km-breadcrumb-link&quot; : &quot;text-secondary-text&quot;" @click="showBackButton &amp;&amp; navigate(parentRoute)">{{ typeof route.meta?.pageLabel === 'function' ? route.meta.pageLabel() : route.meta?.pageLabel }}</span>
          <km-glyph v-if="showBackButton" class="text-secondary-text km-breadcrumb-sep" name="chevron_right" size="18px" />
        </div>
        <div class="flex-1 min-w-0 overflow-hidden km-header-slot">
          <component :is="route.meta.headerComponent" v-if="route.meta?.headerComponent" />
        </div>
        <div class="flex-none mr-md">
          <div class="cluster global-search-trigger cursor-pointer px-sm py-xs" data-gap="sm" data-test="global-search-trigger" @click="showSearch = true">
            <km-glyph name="search" size="16px" tone="subtle" /><span class="text-secondary-text km-description">{{ m.common_search() }}</span>
            <div class="global-search-shortcut"><span>{{ isMac ? '⌘K' : 'Ctrl+K' }}</span></div>
          </div>
        </div>
        <global-search v-model="showSearch" />
        <div class="cluster flex-none mr-md" data-wrap="no" data-gap="xs">
          <button
            type="button"
            class="theme-mode-button"
            :data-state="themeMode"
            :aria-pressed="isDarkMode ? 'true' : 'false'"
            :aria-label="themeToggleLabel"
            :title="themeToggleLabel"
            data-test="theme-mode-toggle"
            @click="toggleThemeMode"
          >
            <km-glyph :name="isDarkMode ? 'dark_mode' : 'light_mode'" size="16px" />
          </button>
          <km-btn flat :icon="isFullscreen ? &quot;collapse&quot; : &quot;expand&quot;" icon-size="16px" interaction-tone="brand" size="sm" :tooltip="isFullscreen ? &quot;Exit fullscreen&quot; : &quot;Fullscreen&quot;" @click="toggleFullscreen" />
          <km-btn flat icon="fa-regular fa-circle-question" icon-size="16px" interaction-tone="brand" size="sm" @click="openHelp" />
          <ds-dropdown-menu-root>
            <ds-dropdown-menu-trigger as-child>
              <div data-test="user-menu">
                <km-btn flat icon="user" icon-size="16px" :label="userDisplayName" interaction-tone="brand" size="sm" label-class="km-title" />
              </div>
            </ds-dropdown-menu-trigger>
            <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4" data-test="user-menu-dropdown">
              <ds-dropdown-menu-item @select="navigate(&quot;/profile&quot;)">
                <km-glyph name="user" size="14px" /><span>{{ m.user_profile() }}</span>
              </ds-dropdown-menu-item>
              <ds-dropdown-menu-separator />
              <ds-dropdown-menu-sub>
                <ds-dropdown-menu-sub-trigger>
                  <km-glyph name="globe" size="14px" /><span>{{ currentLocaleLabel }}</span>
                </ds-dropdown-menu-sub-trigger>
                <ds-dropdown-menu-sub-content :side-offset="4" data-test="locale-menu">
                  <ds-dropdown-menu-item v-for="opt in localeOptions" :key="opt.value" :class="{ 'locale-active': opt.value === locale }" @select="setLocale(opt.value)">
                    {{ opt.label }}
                  </ds-dropdown-menu-item>
                </ds-dropdown-menu-sub-content>
              </ds-dropdown-menu-sub>
              <ds-dropdown-menu-separator />
              <ds-dropdown-menu-item @select="logout">
                <km-glyph name="sign-out" size="14px" /><span>{{ m.auth_logout() }}</span>
              </ds-dropdown-menu-item>
            </ds-dropdown-menu-content>
          </ds-dropdown-menu-root>
        </div>
      </div>
    </header>
    <km-drawer v-model="drawerVisible" class="text-white" :width="sidebarWidth" :breakpoint="0" bordered :behavior="&quot;desktop&quot;">
      <toolbar />
    </km-drawer>
    <div class="km-page-container">
      <workspace-tab-bar />
      <div class="km-view-height" :class="{ &quot;has-tabs&quot;: hasOpenTabs }">
        <router-view v-slot="{ Component, route }">
          <keep-alive :max="20">
            <component :is="Component" v-if="!loading" :key="route.fullPath" />
          </keep-alive>
        </router-view>
      </div>
    </div>
  </div>
  <km-popup-confirm :visible="showLeaveConfirm" :confirm-button-label="m.common_saveChanges()" :confirm-button-label2="m.common_dontSaveChanges()" confirm-button-type2="secondary" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="saveChanges" @cancel="cancelLeave" @confirm2="confirmLeave">
    <div class="cluster km-heading-7 mb-md" data-justify="center">{{ m.workspace_unsavedChanges() }}</div>
    <div class="cluster" data-justify="center">{{ m.workspace_unsavedPageMessage() }}</div>
  </km-popup-confirm>
</template>

<script>
import { useState, useAuth } from '@shared'
import { useLocale } from '@shared/i18n'
import { m } from '@/paraglide/messages'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { ref, computed, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue'
import { useLoading } from '@ds/composables/useLoading'
import { useQueryClient } from '@tanstack/vue-query'
import { useSidebarState } from '@/composables/useSidebarState'
import { useAppStore } from '@/stores/appStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { useKnowledgeGraphPageStore } from '@/stores/entityDetailStores'
import { usePopupStore } from '@/stores/popupStore'
import { useEntitySaveService } from '@/services/entitySaveService'
import { ROUTE_ENTITY_TO_BUFFER_TYPE } from '@/constants/entityMapping'
import WorkspaceTabBar from './Layouts/WorkspaceTabBar.vue'
import GlobalSearch from './Layouts/GlobalSearch.vue'

const THEME_MODE_STORAGE_KEY = 'ds:theme'

function getCurrentThemeMode() {
  const current = document.documentElement.dataset.theme
  if (current === 'dark' || current === 'light') return current

  const stored = localStorage.getItem(THEME_MODE_STORAGE_KEY)
  return stored === 'dark' ? 'dark' : 'light'
}

export default {
  components: { WorkspaceTabBar, GlobalSearch },
  setup() {
    const instance = getCurrentInstance()
    const loading = useState('globalLoading')
    const appStore = useAppStore()
    const { logout } = useAuth()
    const authStore = useSharedAuthStore()
    const userDisplayName = computed(() => {
      const u = authStore.userInfo
      if (!u) return ''
      return u.name || u.email || u.preferred_username || ''
    })
    const workspace = useWorkspaceStore()
    const editBuffer = useEditBufferStore()
    const knowledgeGraphPageStore = useKnowledgeGraphPageStore()
    const popupStore = usePopupStore()
    const saveService = useEntitySaveService()
    const environment = appStore.config.environment
    const { sidebarWidth, isCollapsed, toggle } = useSidebarState()
    const hasOpenTabs = computed(() => workspace.tabs.length > 0)
    const showSearch = ref(false)
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
    const themeMode = ref(getCurrentThemeMode())
    const isDarkMode = computed(() => themeMode.value === 'dark')
    const themeToggleLabel = computed(() => (isDarkMode.value ? 'Switch to light theme' : 'Switch to dark theme'))

    const syncThemeMode = () => {
      themeMode.value = getCurrentThemeMode()
    }

    const applyThemeModeFallback = (mode) => {
      localStorage.setItem(THEME_MODE_STORAGE_KEY, mode)
      document.documentElement.dataset.theme = mode
      document.documentElement.style.colorScheme = mode
      document.body.dataset.colorMode = mode
      document.getElementById('km-app')?.setAttribute('data-color-mode', mode)
    }

    const toggleThemeMode = () => {
      const nextMode = isDarkMode.value ? 'light' : 'dark'
      themeMode.value = nextMode
      const setTheme = instance?.proxy?.$setTheme

      if (typeof setTheme === 'function') {
        setTheme(nextMode)
      } else {
        applyThemeModeFallback(nextMode)
      }
    }

    const { locale, setLocale, locales } = useLocale()
    const localeFullLabels = {
      en: 'English',
      ru: 'Русский',
      lv: 'Latviešu',
      es: 'Español',
      fr: 'Français',
      de: 'Deutsch',
      it: 'Italiano',
      fi: 'Suomi',
      nl: 'Nederlands',
      no: 'Norsk',
      sv: 'Svenska',
      uk: 'Українська',
    }
    const localeLabels = { en: 'EN', ru: 'RU', lv: 'LV', es: 'ES', fr: 'FR', de: 'DE', it: 'IT', fi: 'FI', nl: 'NL', no: 'NO', sv: 'SV', uk: 'UK' }
    const localeOrder = ['en', 'fi', 'nl', 'no', 'sv', 'lv', 'es', 'fr', 'de', 'ru', 'it', 'uk']
    const localeOptions = computed(() =>
      localeOrder
        .filter((loc) => locales.includes(loc))
        .concat(locales.filter((loc) => !localeOrder.includes(loc)))
        .map((loc) => ({ value: loc, label: localeFullLabels[loc] || loc }))
    )
    const currentLocaleLabel = computed(() => localeLabels[locale.value] || locale.value)

    const isFullscreen = ref(!!document.fullscreenElement)
    const toggleFullscreen = () => {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        document.documentElement.requestFullscreen()
      }
    }
    const onFullscreenChange = () => {
      isFullscreen.value = !!document.fullscreenElement
    }

    const onGlobalKeydown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        showSearch.value = true
      }
    }
    onMounted(() => {
      syncThemeMode()
      document.addEventListener('keydown', onGlobalKeydown)
      document.addEventListener('fullscreenchange', onFullscreenChange)
      window.addEventListener('storage', syncThemeMode)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', onGlobalKeydown)
      document.removeEventListener('fullscreenchange', onFullscreenChange)
      window.removeEventListener('storage', syncThemeMode)
    })

    const queryClient = useQueryClient()

    return {
      loading,
      editBuffer,
      knowledgeGraphPageStore,
      popupStore,
      saveService,
      m,
      queryClient,
      drawerVisible: ref(true),
      environment,
      sidebarWidth,
      isCollapsed,
      toggleSidebar: toggle,
      hasOpenTabs,
      logout,
      userDisplayName,
      showSearch,
      isMac,
      themeMode,
      isDarkMode,
      themeToggleLabel,
      toggleThemeMode,
      isFullscreen,
      toggleFullscreen,
      locale,
      setLocale,
      localeOptions,
      currentLocaleLabel,
    }
  },
  computed: {
    showBackButton() {
      if (this.route.name === 'Conversation') return false
      if (this.route.name === 'McpToolsDetail') return false
      if (this.route.name === 'EvaluationCompare') return true
      if (this.route.params.id) return true
      return false
    },
    showPageLabel() {
      return true
    },
    showLeaveConfirm() {
      return this.popupStore.showLeaveConfirm
    },
    nextRoute() {
      return this.popupStore.nextRoute
    },
    parentRoute() {
      const segments = this.route.path.split('/')
      if (segments[1] === 'observability') {
        return `/${segments[1]}/${segments[2]}`
      }
      if (segments[1] === 'evaluation') {
        return `/evaluation-jobs`
      }
      if (segments[1] === 'knowledge-sources') {
        const bufferKey = this.editBuffer.findBufferKeyByEntityType(ROUTE_ENTITY_TO_BUFFER_TYPE['collections'] || 'collections')
        const draft = bufferKey ? this.editBuffer.getDraft(bufferKey) : null
        const providerSystemName = draft?.provider_system_name
        if (providerSystemName) {
          // Find provider ID and category from TanStack Query cache
          const cached = this.queryClient.getQueriesData({ queryKey: ['provider'] })
          for (const [, data] of cached) {
            const items = data?.data ?? data?.items ?? (Array.isArray(data) ? data : [])
            const provider = items.find?.((p) => p?.system_name === providerSystemName)
            if (provider?.id) {
              const prefix = provider.category === 'knowledge' ? 'knowledge-providers' : 'model-providers'
              return `/${prefix}/${provider.id}`
            }
          }
        }
        return `/${segments[1]}`
      }
      if (segments[1] === 'deep-research' && segments[2] === 'runs') {
        return `/deep-research/runs`
      }
      if (segments[1] === 'deep-research' && segments[2] === 'configs') {
        return `/deep-research/configs`
      }
      if (segments[1] === 'note-taker' && segments[2]) {
        return `/note-taker`
      }
      if (segments[1] === 'knowledge-graph' && segments[3] === 'documents') {
        return `/knowledge-graph/${segments[2]}?tab=explorer`
      }
      return `/${segments[1]}`
    },
    route() {
      return this.$route
    },
    routeChromaEntity() {
      return this.route.meta?.entity
    },
  },
  watch: {
    loading: {
      immediate: true,
      handler(val) {
        const ds = useLoading()
        if (val) {
          this._dsLoadingHide = ds.show()
        } else if (this._dsLoadingHide) {
          this._dsLoadingHide()
          this._dsLoadingHide = null
        }
      },
    },
  },
  created() {},
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openHelp() {
      window.open('/help/docs/en/', '_blank')
    },
    confirmLeave() {
      if (!this.nextRoute) return

      if (this.routeChromaEntity === 'knowledge_graph') {
        this.knowledgeGraphPageStore.revertChanges()
      } else if (this.routeChromaEntity) {
        this.saveService.revert(this.routeChromaEntity)
      }

      const target = this.nextRoute
      this.popupStore.hidePopup()
      this.$router.push(target)
    },
    async saveChanges() {
      try {
        if (this.routeChromaEntity === 'knowledge_graph') {
          await this.knowledgeGraphPageStore.saveKnowledgeGraph()
        } else if (this.routeChromaEntity) {
          const result = await this.saveService.save(this.routeChromaEntity)
          if (!result.success) return
        }
      } catch (error) {
        // Save failed — stay on the page
        return
      }

      if (this.nextRoute) {
        const target = this.nextRoute
        this.popupStore.hidePopup()
        this.$router.push(target)
      }
    },
    cancelLeave() {
      this.popupStore.hidePopup()
    },
  },
}
</script>

<style>
.km-underline:hover {
  text-decoration: underline;
  cursor: pointer;
}
.km-breadcrumb-link {
  cursor: pointer;
  transition: var(--ds-transition-opacity);
}
.km-breadcrumb-link:hover {
  opacity: 0.8;
}
.km-breadcrumb-sep {
  opacity: 0.35;
}
.global-search-trigger {
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 6px;
  padding: 4px 12px;
  transition: border-color var(--ds-duration-fast) var(--ds-ease-out);
}
.global-search-trigger:hover {
  border-color: rgba(0,0,0,0.25);
}
.global-search-shortcut {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(0,0,0,0.12);
  font-size: 11px;
  color: var(--ds-color-secondary-text);
  margin-inline-start: 8px;
}
.theme-mode-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 32px;
  block-size: 32px;
  padding: 0;
  background: transparent;
  border: 0;
  border-radius: var(--ds-radius-md);
  color: var(--ds-color-secondary-text);
  cursor: pointer;
  transition: var(--ds-transition-colors);
}
.theme-mode-button:hover {
  background: var(--ds-color-primary-bg);
  color: var(--ds-color-primary);
}
.theme-mode-button:focus-visible {
  outline: 2px solid var(--ds-color-primary);
  outline-offset: 2px;
}
/* Layout contract for the admin shell.

   Visual structure (after the Quasar→Reka migration):

       .km-layout (CSS grid: header / drawer + page)
         header.km-header        — full-width top bar
         km-drawer (collapsing)  — left sidebar
         .km-page-container      — main content area, scroll-owner

   `html > body > #km-app` each have `height: 100%` (index.html) so the
   chain from viewport to page content is never broken. Every level of
   the page-container chain bounds its children's height with `min-height:
   0; overflow: hidden` so a single inner `overflow: auto` (the table or
   page content) is the sole scroll owner. */
.km-layout {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto 1fr;
  block-size: 100%;
  inline-size: 100%;
  min-block-size: 0;
}
.km-layout > .km-header {
  grid-column: 1/-1;
  grid-row: 1;
}
.km-layout > .km-drawer {
  grid-column: 1;
  grid-row: 2;
  block-size: 100%;
}
.km-layout > .km-page-container {
  grid-column: 2;
  grid-row: 2;
  min-inline-size: 0;
}
.km-page-container {
  display: flex;
  flex-direction: column;
  block-size: 100%;
  min-block-size: 0;
  overflow: hidden;
}
.km-view-height {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-block-size: 0;
  block-size: 100%;
  overflow: hidden;
}
.km-sidebar-header {
  overflow: hidden;
  transition: width var(--ds-duration-base) var(--ds-ease-out);
}
.locale-active {
  color: var(--ds-color-primary) !important;
  font-weight: 500;
}
.km-sidebar-toggle {
  opacity: 0.6;
  transition: var(--ds-transition-opacity);
}
.km-sidebar-toggle:hover {
  opacity: 1;
}

.km-header__bar {
  block-size: 50px;
}

.km-header__env-tag {
  inset-block-end: 0;
  inset-inline-end: 6px;
}
</style>
