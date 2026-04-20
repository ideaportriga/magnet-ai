<template lang="pug">
km-inner-loading(:showing='loading')
layouts-details-layout(v-if='!loading', :contentContainerStyle='{ maxWidth: "1200px", margin: "0 auto" }')
  template(#header)
    .col
      .row.items-center
        km-input-flat.km-heading-4.full-width.text-black(data-test='name-input', :placeholder='m.common_name()', :model-value='name', @change='name = $event')
      .row.items-center.q-pl-6
        q-icon.col-auto(name='o_info', color='text-secondary')
          q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ m.tooltip_systemNameUniqueId() }}
        km-input-flat.col.km-description.text-black.full-width(
          data-test='system-name-input',
          :placeholder='m.placeholder_enterSystemNameReadable()',
          :model-value='system_name',
          @change='system_name = $event',
          @focus='showInfo = true',
          @blur='showInfo = false'
        )
      .km-description.text-secondary.q-pl-6(v-if='showInfo') {{ m.hint_systemNameRecommendation() }}
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ updated_by }}
    km-btn(data-test='revert-btn', :label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(data-test='save-btn', :label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='handleSave', :loading='saving', :disable='saving || !isDirty')
    q-btn.q-px-xs(data-test='show-more-btn', flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(data-test='clone-btn', clickable, @click='showNewDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(data-test='delete-btn', clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.deleteConfirm_deleteEntity({ entity: m.entity_knowledgeSourceProvider() })',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: m.entity_knowledgeSourceProvider() }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_knowledgeSourceProvider() }) }}
  template(#content)
    .column.full-height(style='min-height: 0')
      q-tabs.bb-border.full-width(
        v-model='tab',
        narrow-indicator,
        dense,
        align='left',
        active-color='primary',
        indicator-color='primary',
        active-bg-color='white',
        no-caps,
        content-class='km-tabs'
      )
        template(v-for='t in tabs')
          q-tab(:name='t.name', :label='t.label')
      .col(style='min-height: 0; padding-top: 16px; padding-bottom: 16px')
        knowledge-providers-knowledge-sources(v-if='tab == "knowledge-sources"')
        knowledge-providers-settings(v-if='tab == "settings"')
</template>

<script>
import { computed, ref } from 'vue'
import { beforeRouteEnter } from '@/guards'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'

export default {
  beforeRouteEnter,
  setup() {
    const { draft, isLoading, isDirty, updateField, revert, save, remove } = useEntityDetail('provider')

    const loading = computed(() => isLoading.value || !draft.value)

    return {
      m,
      draft,
      loading,
      isDirty,
      updateField,
      revert,
      saveEntity: save,
      removeEntity: remove,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showNewDialog: ref(false),
      tab: ref('knowledge-sources'),
      tabs: ref([
        { name: 'knowledge-sources', label: m.section_knowledgeSources() },
        { name: 'settings', label: m.common_settings() },
      ]),
      showInfo: ref(false),
    }
  },
  computed: {
    provider() {
      return this.draft
    },
    name: {
      get() {
        return this.provider?.name || ''
      },
      set(value) {
        this.updateField('name', value)
      },
    },
    system_name: {
      get() {
        return this.provider?.system_name || ''
      },
      set(value) {
        this.updateField('system_name', value)
      },
    },
    created_at() {
      return this.provider?.created_at ? this.formatDate(this.provider.created_at) : ''
    },
    modified_at() {
      return this.provider?.updated_at ? this.formatDate(this.provider.updated_at) : ''
    },
    created_by() {
      return this.provider?.created_by || 'Unknown'
    },
    updated_by() {
      return this.provider?.updated_by || 'Unknown'
    },
  },
  methods: {
    async handleSave() {
      this.saving = true
      try {
        const { success, error } = await this.saveEntity()
        if (success) {
          notify.success('Saved successfully')
        } else {
          throw error || new Error('Failed to save')
        }
      } catch (error) {
        notify.error(error.message || 'Failed to save')
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      const { success } = await this.removeEntity()
      if (success) {
        notify.success('Knowledge Provider has been deleted.')
        this.$router.push('/knowledge-providers')
      }
    },
    formatDate(date) {
      const d = new Date(date)
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
    },
  },
}
</script>
