<template lang="pug">
q-layout.bg-light.full-height.overflow-hidden(view='hHh lpR fFf')
  q-header
    .row.bg-white.text-black.items-center.no-wrap.bb-border(style='height: 50px', data-test='header')
      .col-auto.full-height.br-border.row.nowrap.items-center.justify-center.km-sidebar-header(
        :style='{ width: sidebarWidth + "px", transition: "width 0.2s ease" }'
      )
        .row.no-wrap.q-gap-8.cursor-pointer.items-center.full-height(v-if='!isCollapsed', @click='navigate("/")')
          km-icon(:name='"magnet"', width='20', height='23')
          .relative-position
            .km-heading-6.logo-text Magnet AI
            .absolute(style='bottom: 0px; right: 6px')
              .logo-text {{ environment }}
        .row.cursor-pointer.items-center.justify-center.full-height(v-else, @click='navigate("/")')
          km-icon(:name='"magnet"', width='20', height='23')
      //- Sidebar toggle
      q-icon.col-auto.cursor-pointer.q-ml-md.km-sidebar-toggle(
        name='fas fa-table-columns',
        size='16px',
        color='secondary-text',
        @click.stop='toggleSidebar'
      )
      .col-auto.q-mx-md.row.items-center.no-wrap.q-gap-8(v-if='showPageLabel || showBackButton')
        span.km-body.km-breadcrumb-item(
          :class='showBackButton ? "text-primary km-breadcrumb-link" : "text-secondary-text"',
          @click='showBackButton && navigate(parentRoute)'
        ) {{ route.meta?.pageLabel }}
        q-icon.text-secondary-text.km-breadcrumb-sep(v-if='showBackButton', name='chevron_right', size='18px')
      component(v-if='route.meta?.headerComponent', :is='route.meta.headerComponent')
      .col
      //- Global search trigger
      .col-auto.q-mr-md
        .global-search-trigger.row.items-center.q-gap-8.cursor-pointer.q-px-sm.q-py-xs(@click='showSearch = true')
          q-icon(name='search', size='16px', color='secondary-text')
          span.text-secondary-text.km-description Search
          .global-search-shortcut
            span {{ isMac ? '⌘K' : 'Ctrl+K' }}
      global-search(v-model='showSearch')
      //- Right-side header actions: Fullscreen + Help + Profile
      .col-auto.row.items-center.no-wrap.q-gap-4.q-mr-md
        km-btn(flat, :icon='isFullscreen ? "fas fa-compress" : "fas fa-expand"', iconSize='16px', iconColor='icon', hoverColor='primary', hoverBg='primary-bg', size='sm', :tooltip='isFullscreen ? "Exit fullscreen" : "Fullscreen"', @click='toggleFullscreen')
        km-btn(flat, icon='fa-regular fa-circle-question', iconSize='16px', iconColor='icon', label='Help', hoverColor='primary', hoverBg='primary-bg', size='sm', labelClass='km-title', @click='openHelp')
        .relative-position
          km-btn(flat, icon='fas fa-user-circle', iconSize='16px', iconColor='icon', :label='userDisplayName', hoverColor='primary', hoverBg='primary-bg', size='sm', labelClass='km-title')
          q-menu(anchor='bottom right', self='top right', :offset='[0, 4]')
            q-list(dense, style='min-width: 180px')
              q-item.km-nav-popup-item(clickable, v-close-popup, @click='navigate("/profile")')
                q-item-section(avatar, style='min-width: 28px; padding-right: 4px')
                  q-icon(name='fas fa-user', size='14px', color='icon')
                q-item-section Profile
              q-item.km-nav-popup-item(clickable, v-close-popup, @click='logout')
                q-item-section(avatar, style='min-width: 28px; padding-right: 4px')
                  q-icon(name='fas fa-sign-out-alt', size='14px', color='icon')
                q-item-section Log out
  q-drawer.text-white(
    v-model='drawerVisible',
    :width='sidebarWidth',
    :breakpoint='0',
    bordered,
    :behavior='"desktop"'
  )
    toolbar
  q-page-container
    workspace-tab-bar
    .km-view-height(:class='{ "has-tabs": hasOpenTabs }')
      router-view(v-slot='{ Component, route }')
        keep-alive(:max='20')
          component(v-if='!loading', :is='Component', :key='route.fullPath')
km-popup-confirm(
  :visible='showLeaveConfirm',
  confirmButtonLabel='Save changes',
  confirmButtonLabel2='Don\'t save changes',
  confirmButtonType2='secondary',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='saveChanges',
  @cancel='cancelLeave',
  @confirm2='confirmLeave'
)
  .row.item-center.justify-center.km-heading-7.q-mb-md Unsaved Changes
  .row.text-center.justify-center You have unsaved changes here. Please choose what you would like to do.
</template>

<script>
import { useState, useAuth } from '@shared'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
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

export default {
  components: { WorkspaceTabBar, GlobalSearch },
  setup() {
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
      document.addEventListener('keydown', onGlobalKeydown)
      document.addEventListener('fullscreenchange', onFullscreenChange)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', onGlobalKeydown)
      document.removeEventListener('fullscreenchange', onFullscreenChange)
    })

    return {
      loading,
      editBuffer,
      knowledgeGraphPageStore,
      popupStore,
      saveService,
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
      isFullscreen,
      toggleFullscreen,
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
        return providerSystemName ? `/knowledge-providers/${providerSystemName}` : `/${segments[1]}`
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
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
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

      this.$router.push(this.nextRoute)
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
        this.$router.push(this.nextRoute)
      }
    },
    cancelLeave() {
      this.popupStore.hidePopup()
    },
  },
}
</script>

<style lang="stylus">
.km-underline:hover {
  text-decoration: underline;
  cursor: pointer;
}

.km-breadcrumb-link {
  cursor: pointer;
  transition: opacity 0.15s ease;
  &:hover {
    opacity: 0.8;
  }
}

.km-breadcrumb-sep {
  opacity: 0.35;
}

.global-search-trigger {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  padding: 4px 12px;
  transition: border-color 0.15s ease;
  &:hover {
    border-color: rgba(0, 0, 0, 0.25);
  }
}

.global-search-shortcut {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  font-size: 11px;
  color: var(--q-secondary-text);
  margin-left: 8px;
}

.km-view-height {
    max-height: calc(100vh - 50px) !important;
    height: calc(100vh - 50px) !important;
    overflow: hidden;
    &.has-tabs {
      max-height: calc(100vh - 88px) !important;
      height: calc(100vh - 88px) !important;
    }
}

.km-sidebar-header {
  overflow: hidden;
  transition: width 0.2s ease;
}

.km-sidebar-toggle {
  opacity: 0.6;
  transition: opacity 0.15s ease;
  &:hover {
    opacity: 1;
  }
}
</style>
