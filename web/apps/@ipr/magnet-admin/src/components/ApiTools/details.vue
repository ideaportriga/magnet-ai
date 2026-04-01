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
    km-btn(label='Record info', flat, icon='info', iconSize='16px')
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ metadata.created_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Modified:
            .text-secondary-text.km-description {{ metadata.modified_at }}
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created by:
            .text-secondary-text.km-description {{ metadata.created_by }}
          div
            .text-secondary-text.km-button-xs-text Modified by:
            .text-secondary-text.km-description {{ metadata.updated_by }}
    km-btn(label='Revert', icon='fas fa-undo', iconSize='16px', flat, @click='apiToolStore.revert()', v-if='apiToolStore.isChanged')
    km-btn(label='Save', flat, icon='far fa-save', iconSize='16px', @click='save', :loading='saving', :disable='saving || !apiToolStore.isChanged')
    q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
      q-menu(anchor='bottom right', self='top right')
        q-item(clickable, @click='clone', dense)
          q-item-section
            .km-heading-3 Clone
        q-item(clickable, @click='showDeleteDialog = true', dense)
          q-item-section
            .km-heading-3 Delete
    km-popup-confirm(
      :visible='showDeleteDialog',
      confirmButtonLabel='Delete API Tool',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='confirmDelete',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete the API Tool
      .row.text-center.justify-center This action will permanently delete the API Tool and disable it in all tools that are using it, e.g. Agents.
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
import { ref, computed, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useApiServerDetailStore, useApiToolDetailStore } from '@/stores/entityDetailStores'
import _ from 'lodash'
export default {
  setup() {
    const route = useRoute()
    const queries = useEntityQueries()
    const apiServerStore = useApiServerDetailStore()
    const apiToolStore = useApiToolDetailStore()
    const id = ref(route.params.id)
    onActivated(() => { id.value = route.params.id })

    const { data: apiServersData } = queries.api_servers.useList()
    const items = computed(() => apiServersData.value?.items ?? [])

    const { mutateAsync: updateApiTool } = queries.api_tools.useUpdate()
    const { mutateAsync: removeApiTool } = queries.api_tools.useRemove()
    const { data: apiToolsListData } = queries.api_tools.useList()

    return {
      tab: ref('parameters'),
      tabs: ref([
        { name: 'parameters', label: 'Parameters' },
        { name: 'information', label: 'API Information' },
      ]),
      items,
      openPropDetails: ref(false),
      selectedRow: ref(null),
      apiServerStore,
      apiToolStore,
      updateApiTool,
      removeApiTool,
      apiToolsListData,
      saving: ref(false),
      showDeleteDialog: ref(false),
      showCloneDialog: ref(false),
      clonedTool: ref(null),
    }
  },
  computed: {
    apiServer() {
      return this.items.find((item) => item.id === this.$route.params.id) ?? {}
    },
    apiTool() {
      return this.apiServerStore.entity?.tools?.find((tool) => tool.system_name === this.$route.params.name)
    },
    metadata() {
      return {
        created_at: this.formatDate(this.apiTool?.created_at),
        modified_at: this.formatDate(this.apiTool?.updated_at),
        created_by: this.apiTool?.created_by ? `${this.apiTool?.created_by}` : 'Unknown',
        updated_by: this.apiTool?.updated_by ? `${this.apiTool?.updated_by}` : 'Unknown',
      }
    },
    name: {
      get() {
        return this.apiTool?.name || ''
      },
      set(value) {
        this.apiServerStore.updateNestedProperty({ path: 'name', value, system_name: this.apiTool.system_name })
      },
    },
    description: {
      get() {
        return this.apiTool?.description || ''
      },
      set(value) {
        this.apiServerStore.updateNestedProperty({ path: 'description', value, system_name: this.apiTool.system_name })
      },
    },
    system_name: {
      get() {
        return this.apiTool?.system_name || ''
      },
      set(value) {
        // this.apiServerStore.updateNestedProperty({ path: 'system_name', value, system_name: this.apiTool.system_name })
      },
    },
  },
  watch: {
    apiServer: {
      handler(newVal) {
        if (newVal !== this.apiServerStore.entity) {
          this.apiServerStore.setEntity(_.cloneDeep(newVal))
        }
      },
      deep: true,
      immediate: true,
    },
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
  mounted() {
    // this.apiServerStore.setEntity(_.cloneDeep(this.apiTool))
  },
  activated() {
    // Re-sync Pinia state when KeepAlive reactivates this component (multi-tab support)
    const server = this.apiServer
    if (server && server.id !== this.apiServerStore.entity?.id) {
      this.apiServerStore.setEntity(_.cloneDeep(server))
    }
  },
  methods: {
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
        const data = this.apiToolStore.buildPayload()
        await this.updateApiTool({ id: this.apiToolStore.entity.id, data })
        this.apiToolStore.setInit()
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Saved successfully', timeout: 2000 })
      } catch (error) {
        this.$q.notify({ color: 'red-9', textColor: 'white', icon: 'error', group: 'error', message: 'Failed to save API Tool.', timeout: 2000 })
      } finally {
        this.saving = false
      }
    },
    async confirmDelete() {
      this.saving = true
      try {
        await this.removeApiTool(this.apiTool.id)
        this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'API Tool has been deleted.', timeout: 1000 })
        this.$router?.push('/api-tools')
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
      const items = this.apiToolsListData?.items || []
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
