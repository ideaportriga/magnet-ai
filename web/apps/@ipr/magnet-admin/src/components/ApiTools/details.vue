<template>
  <km-inner-loading :showing="!apiTool" />
  <layouts-details-layout v-if="apiTool" :name="name" :description="description" :system-name="system_name" :created-at="apiTool?.created_at" :updated-at="apiTool?.updated_at" :created-by="apiTool?.created_by" :updated-by="apiTool?.updated_by" show-record-info @update:name="name = $event" @update:description="description = $event" @update:system-name="system_name = $event">
    <template #header-actions>
      <km-btn v-if="isDirty" :label="m.common_revert()" icon="undo" icon-size="16px" flat @click="revert()" />
      <km-btn :label="m.common_save()" flat icon="save" icon-size="16px" :loading="saving" :disable="saving || !isDirty" @click="save" />
      <ds-dropdown-menu-root>
        <ds-dropdown-menu-trigger as-child>
          <km-btn class="px-xs" flat icon="more-vertical" size="13px" />
        </ds-dropdown-menu-trigger>
        <ds-dropdown-menu-content side="bottom" align="end" :side-offset="4">
          <ds-dropdown-menu-item @select="clone">{{ m.common_clone() }}</ds-dropdown-menu-item>
          <ds-dropdown-menu-item variant="destructive" @select="showDeleteDialog = true">{{ m.common_delete() }}</ds-dropdown-menu-item>
        </ds-dropdown-menu-content>
      </ds-dropdown-menu-root>
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.dialog_deleteApiTool()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="confirmDelete" @cancel="showDeleteDialog = false">
        <div class="cluster" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.entity_apiTool() }) }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.deleteConfirm_permanentDeleteDisable({ entity: m.entity_apiTool() }) }}</div>
      </km-popup-confirm>
    </template>
    <template #content>
      <div class="stack full-height" data-gap="0" style="min-block-size: 0">
        <km-tabs v-model="tab" :items="tabs" class="bb-border full-width" narrow-indicator dense align="left" no-caps content-class="km-tabs" />
        <div class="flex-1" style="min-block-size: 0; padding-block: 16px">
          <api-tools-tabs-information v-if="tab == &quot;information&quot;" :api-tool="apiTool" />
          <api-tools-tabs-parameters v-if="tab == &quot;parameters&quot;" :api-tool="apiTool" :selected-row="selectedRow" @select="selectedRow = $event" />
        </div>
      </div>
    </template>
    <template #drawer>
      <api-tools-drawer ref="drawer" :open="openPropDetails" :selected-row="selectedRow" @update:open="openPropDetails = $event" />
    </template>
  </layouts-details-layout>
  <api-tools-clone-dialog :show="showCloneDialog" :tool="clonedTool" @cancel="showCloneDialog = false" />
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityDetail } from '@/composables/useEntityDetail'
import _ from 'lodash'
import { m } from '@/paraglide/messages'
import { notify } from '@shared/utils/notify'
export default {
  setup() {
    const route = useRoute()
    const { draft, isDirty, updateField, save: saveServer, revert } = useEntityDetail('api_servers')

    return {
      m,
      tab: ref('parameters'),
      tabs: ref([
        { value: 'parameters', label: m.apiTools_parameters() },
        { value: 'information', label: m.apiTools_apiInformation() },
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
    async save() {
      this.saving = true
      try {
        const result = await this.saveServer()
        if (result.success) {
          notify.success(m.notify_savedSuccessfully())
        } else {
          throw result.error || new Error('Failed to save')
        }
      } catch (error) {
        notify.error(m.notify_failedToSave())
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
         notify.success(m.notify_deletedSuccessfully({ entity: m.entity_apiTool() }))
        this.$router?.push(`/api-servers/${this.$route.params.id}`)
      } catch (error) {
        const errorMessage = error?.message || m.notify_failedToDelete()
        notify.error(errorMessage)
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
