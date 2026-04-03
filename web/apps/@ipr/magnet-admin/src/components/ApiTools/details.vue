<template lang="pug">
km-inner-loading(:showing='!apiTool')
layouts-details-layout(v-if='apiTool')
  template(#header)
    layouts-details-header(v-model:name='name', v-model:description='description', v-model:systemName='system_name')
    //- q-separator.q-mt-8
    //- .row.items-end.q-pt-8.q-gap-4
    //-   .km-input-label.q-pl-6.text-secondary-text.q-pb-4(style='line-height: 16px') API Provider
      //- km-select-flat(placeholder='API Provider', :options='apiProviderOptions', v-model='apiProvider')
  template(#header-actions)
    km-btn(:label='m.common_recordInfo()', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdLabel() }}
            .text-secondary-text.km-description {{ metadata.created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_modified() }}
            .text-secondary-text.km-description {{ metadata.modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text {{ m.common_createdBy() }}
            .text-secondary-text.km-description {{ metadata.created_by }}
          div
            .text-secondary-text.km-button-xs-text {{ m.common_modifiedBy() }}
            .text-secondary-text.km-description {{ metadata.updated_by }}
    km-btn(:label='m.common_revert()', icon='fas fa-undo', iconSize='16px', flat, @click='revert()', v-if='isDirty')
    km-btn(:label='m.common_save()', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !isDirty')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='clone', dense)
          q-item-section
            .km-heading-3 {{ m.common_clone() }}
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 {{ m.common_delete() }}
    km-popup-confirm(
      :visible='showDeleteDialog',
      :confirmButtonLabel='m.dialog_deleteApiTool()',
      :cancelButtonLabel='m.common_cancel()',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 {{ m.deleteConfirm_aboutToDelete({ entity: 'API Tool' }) }}
      .row.text-center.justify-center {{ m.deleteConfirm_permanentDeleteDisable({ entity: 'API Tool' }) }}
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
        api-tools-tabs-information(v-if='tab == "information"', :apiTool='apiTool')
        api-tools-tabs-parameters(v-if='tab == "parameters"', :apiTool='apiTool', @select='selectedRow = $event', :selectedRow='selectedRow')

  template(#drawer)
    api-tools-drawer(v-model:open='openPropDetails', :selectedRow='selectedRow', ref='drawer')
api-tools-clone-dialog(:show='showCloneDialog', :tool='clonedTool', @cancel='showCloneDialog = false')
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import _ from 'lodash'
import { m } from '@/paraglide/messages'
export default {
  setup() {
    const route = useRoute()
    const { draft, isDirty, updateField, save: saveServer, revert } = useEntityDetail('api_servers')

    return {
      m,
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'information', label: 'API Information' },
      ]),
      openPropDetails: ref(false),
      selectedRow: ref(null),
      draft,
      isDirty,
      updateField,
      saveServer,
      revert,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showCloneDialog: ref(false),
      clonedTool: ref(null),
    }
  },
  computed: {
    apiTool() {
      return this.draft?.tools?.find((tool) => tool.system_name === this.$route.params.name)
    },
    metadata() {
      return {
        created_at: this.formatDate(this.apiTool?.created_at),
        modified_at: this.formatDate(this.apiTool?.updated_at),
        created_by: this.apiTool?.created_by ? `${this.apiTool?.created_by}` : m.common_unknown(),
        updated_by: this.apiTool?.updated_by ? `${this.apiTool?.updated_by}` : m.common_unknown(),
      }
    },
    name: {
      get() {
        return this.apiTool?.name || ''
      },
      set(value) {
        this.updateToolNestedProperty('name', value)
      },
    },
    description: {
      get() {
        return this.apiTool?.description || ''
      },
      set(value) {
        this.updateToolNestedProperty('description', value)
      },
    },
    system_name: {
      get() {
        return this.apiTool?.system_name || ''
      },
      set(value) {
        // system_name should not be changed
      },
    },
  },
  watch: {
    selectedRow: {
      handler() {
        this.$refs.drawer?.setTab('details')
      },
      deep: true,
    },
    tab: {
      handler(newVal) {
        this.$refs.drawer?.regulateTabs(newVal)
      },
      immediate: true,
    },
  },
  methods: {
    updateToolNestedProperty(path, value) {
      const tools = this.draft?.tools
      if (!tools) return
      const toolIndex = tools.findIndex((t) => t.system_name === this.$route.params.name)
      if (toolIndex === -1) return
      this.updateField(`tools.${toolIndex}.${path}`, value)
    },
    navigate(path) {
      this.$router.push(path)
    },
    formatDate(date) {
      if (!date) return ''
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
    async save() {
      this.saving = true
      try {
        const result = await this.saveServer()
        if (result.success) {
          this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: m.notify_savedSuccessfully(), timeout: 2000 })
        } else {
          throw result.error || new Error('Failed to save')
        }
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: m.notify_failedToSave(), timeout: 2000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      this.saving = true
      try {
        const tools = this.draft?.tools
        if (!tools) throw new Error('No tools found')
        const toolIndex = tools.findIndex((t) => t.system_name === this.$route.params.name)
        if (toolIndex === -1) throw new Error('Tool not found')
        this.updateField('tools', tools.filter((_, i) => i !== toolIndex))
        const result = await this.saveServer()
        if (!result.success) throw result.error || new Error('Failed to save')
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: m.notify_deletedSuccessfully({ entity: 'API Tool' }), timeout: 1000 })
        this.$router?.push(`/api-servers/${this.$route.params.id}`)
      } catch (error) {
        const errorMessage = error?.message || 'Failed to delete API Tool.'
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: errorMessage, timeout: 3000 })
      } finally {
        this.saving = false
      }
    },
    async clone() {
      const newTool = _.cloneDeep(this.apiTool)
      delete newTool._metadata
      delete newTool.id
      newTool.system_name = newTool.system_name + '_COPY'
      let i = 2
      const items = this.draft?.tools || []
      while (items.some((item) => item.system_name === newTool.system_name)) {
        i++
        newTool.system_name = `${this.apiTool.system_name}_COPY_${i}`
      }
      this.clonedTool = newTool
      this.showCloneDialog = true
    },
  },
}
</script>
