<template lang="pug">
km-inner-loading(:showing='loading')
.row.no-wrap.overflow-hidden.full-height(v-if='!loading', style='min-width: 1200px')
  .col.row.no-wrap.full-height.justify-center.fit
    .col(style='max-width: 1200px; min-width: 600px')
      .full-height.q-pb-md.relative-position.q-px-md
        .row.items-center.q-gap-12.no-wrap.full-width.q-mt-lg.q-mb-sm.bg-white.border-radius-8.q-py-12.q-px-16
          .col
            .row.items-center
              km-input-flat.km-heading-4.full-width.text-black(placeholder='Name', :modelValue='name', @change='name = $event')
            .row.items-center
              km-input-flat.km-description.full-width.text-black(
                placeholder='Description',
                :modelValue='description',
                @change='description = $event'
              )
            .row.items-center.q-pl-6
              q-icon.col-auto(name='o_info', color='text-secondary')
                q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') System name serves as unique record id
              km-input-flat.col.km-description.text-black.full-width.text-black(
                placeholder='Enter system name',
                :modelValue='system_name',
                @change='system_name = $event',
                @focus='showInfo = true',
                @blur='showInfo = false'
              )
            .km-description.text-secondary.q-pl-6(v-if='showInfo') It is highly recommended to fill in system name only once and not change it later.
          .col-auto.row.items-center.no-wrap.q-gap-8.q-ml-md
            km-btn(label='Record info', flat, icon='info', iconSize='16px')
              q-tooltip.bg-white.block-shadow
                .q-pa-sm
                  .q-mb-sm
                    .text-secondary-text.km-button-xs-text Created:
                    .text-secondary-text.km-description {{ created_at }}
                  .q-mb-sm
                    .text-secondary-text.km-button-xs-text Modified:
                    .text-secondary-text.km-description {{ modified_at }}
                  .q-mb-sm
                    .text-secondary-text.km-button-xs-text Created by:
                    .text-secondary-text.km-description {{ created_by }}
                  div
                    .text-secondary-text.km-button-xs-text Modified by:
                    .text-secondary-text.km-description {{ updated_by }}
            km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
            km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !isDirty')
            q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
              q-menu(anchor='bottom right', self='top right')
                q-item(clickable, @click='showNewDialog = true', dense)
                  q-item-section
                    .km-heading-3 Clone
                q-item(clickable, @click='showDeleteDialog = true', dense)
                  q-item-section
                    .km-heading-3 Delete
            km-popup-confirm(
              :visible='showDeleteDialog',
              confirmButtonLabel='Delete AI App',
              cancelButtonLabel='Cancel',
              notificationIcon='fas fa-triangle-exclamation',
              @confirm='confirmDelete',
              @cancel='showDeleteDialog = false'
            )
              .row.item-center.justify-center.km-heading-7 You are about to delete the AI App
              .row.text-center.justify-center This action will permanently delete the AI App and its AI Tabs.

        .ba-border.bg-white.border-radius-12.q-pa-16(style='min-width: 300px')
          q-tabs.bb-border.full-width(
            v-model='folderTab',
            narrow-indicator,
            dense,
            align='left',
            active-color='primary',
            indicator-color='primary',
            active-bg-color='white',
            no-caps,
            content-class='km-tabs'
          )
            template(v-for='t in folderTabs')
              q-tab(:name='t.name', :label='t.label')
          .column.no-wrap.q-gap-16.full-height.full-width.overflow-auto.q-my-md.km-scroll-area-lg
            .row.q-gap-16.full-height.full-width
              .col.full-height.full-width
                .column.items-center.full-height.full-width.q-gap-16.overflow-auto
                  .col-auto.full-width
                    template(v-if='folderTab == "records"')
                      ai-apps-records
                    template(v-if='folderTab == "settings"')
                      ai-apps-settings

  .col-auto(v-if='tabs.length > 0')
    ai-apps-drawer(v-model:open='openTest')
ai-apps-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
</template>

<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
import { VueDraggable } from 'vue-draggable-plus'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useSearchStore } from '@/stores/searchStore'
import { storeToRefs } from 'pinia'

export default {
  components: {
    VueDraggable,
  },
  emits: ['update:closeDrawer'],
  setup() {
    const { draft, isLoading, isDirty, updateField, updateFields, save: saveEntity, revert, refetch, remove, buildPayload } = useEntityDetail('ai_apps')
    const queries = useEntityQueries()
    const searchStore = useSearchStore()
    const { semanticSearchAnswers } = storeToRefs(searchStore)
    function clearSemanticSearchAnswers() {
      semanticSearchAnswers.value = []
    }
    const { mutateAsync: createEntity } = queries.ai_apps.useCreate()

    return {
      draft,
      isLoading,
      isDirty,
      updateField,
      updateFields,
      saveEntity,
      revert,
      refetch,
      removeEntity: remove,
      buildPayload,
      activeAIApp: ref({}),
      prompt: ref(null),
      openTest: ref(true),
      openCreateDialog: ref(true),
      showInfo: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
      saving: ref(false),
      createEntity,
      searchString: ref(''),
      hovered: ref({}),
      isMoving: ref(false),
      clickedRow: ref({}),
      folderTab: ref('records'),
      folderTabs: ref([
        { name: 'records', label: 'AI Tabs' },
        { name: 'settings', label: 'Settings' },
      ]),
      clearSemanticSearchAnswers,
    }
  },
  computed: {
    name: {
      get() {
        return this.draft?.name || ''
      },
      set(value) {
        this.updateField('name', value)
      },
    },
    description: {
      get() {
        return this.draft?.description || ''
      },
      set(value) {
        this.updateField('description', value)
      },
    },
    system_name: {
      get() {
        return this.draft?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    tabs: {
      get() {
        return this.draft?.tabs || []
      },
      set(value) {
        this.updateField('tabs', value)
      },
    },
    searchedTabs: {
      get() {
        return this.tabs.filter((tab) => tab.name.toLowerCase().includes(this.searchString.toLowerCase()))
      },
      set(value) {
        this.tabs = value
      },
    },
    activeAIAppId() {
      return this.$route.params?.id
    },
    loading() {
      return !this.draft?.id
    },
    entity() {
      return this.draft
    },
    created_at() {
      return this.entity?.created_at ? this.formatDate(this.entity.created_at) : ''
    },
    modified_at() {
      return this.entity?.updated_at ? this.formatDate(this.entity.updated_at) : ''
    },
    created_by() {
      return this.entity?.created_by || 'Unknown'
    },
    updated_by() {
      return this.entity?.updated_by || 'Unknown'
    },
  },
  methods: {
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    openTabDetails(row) {
      // Tab context passed via URL param; no Vuex needed
      this.navigate(`${this.$route.path}/items/${row.system_name}`)
    },
    async save() {
      this.saving = true
      try {
        if (this.entity?.created_at) {
          await this.saveEntity()
        } else {
          await this.createEntity(this.entity)
        }
        // Refresh the iframe
        window.postMessage({ type: 'reload_iframe' })
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: error.message || 'Failed to save', timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      await this.removeEntity()
      this.$emit('update:closeDrawer', null)
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'AI App has been deleted.', timeout: 1000 })
      this.navigate('/ai-apps')
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
    },
  },
}
</script>

<style lang="stylus">
.gradient {
  background: linear-gradient(121.5deg, var(--q-primary) 9.69%, var(--q-error) 101.29%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

@keyframes wobble {
    0% { transform: rotate(-5deg); }
    50% { transform: rotate(5deg); }
    100% { transform: rotate(-5deg); }
}

.wobble {
    animation: wobble 2s infinite;
}

.card-hover:hover  {
  background: var(--q-background)
  cursor pointer
  border-color: var(--q-primary)
}
</style>
