<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ selectedTool?.name }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
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
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='clone', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete
q-inner-loading(:showing='loading')
api-tools-clone-dialog(:show='showCloneDialog', :tool='clonedTool', @cancel='showCloneDialog = false')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete API Tool',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteTool',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the API Tool
  .row.text-center.justify-center This action will permanently delete the API Tool and disable it in all tools that are using it, e.g. Agents.
</template>

<script>
import { useChroma } from '@shared'
import _ from 'lodash'
import { ref } from 'vue'
export default {
  setup() {
    const { items, update, create, ...useApiTools } = useChroma('api_tools')
    const loading = ref(false)
    const showCloneDialog = ref(false)
    const clonedTool = ref(null)
    const showDeleteDialog = ref(false)
    return { items, update, create, useApiTools, loading, showCloneDialog, clonedTool, showDeleteDialog }
  },
  computed: {
    metadata() {
      return {
        created_at: this.formatDate(this.selectedTool?.created_at),
        modified_at: this.formatDate(this.selectedTool?.updated_at),
        created_by: this.selectedTool?.created_by ? `${this.selectedTool?.created_by}` : 'Unknown',
        updated_by: this.selectedTool?.updated_by ? `${this.selectedTool?.updated_by}` : 'Unknown',
      }
    },
    selectedTool() {
      return this.$store.getters.api_tool
    },
    createdAt() {
      if (!this.selectedTool?.created_at) return ''
      return this.formatDate(this.selectedTool?.created_at)
    },
    modifiedAt() {
      if (!this.selectedTool?.updated_at) return ''
      return this.formatDate(this.selectedTool?.updated_at)
    },
  },
  methods: {
    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
    deleteTool() {
      this.useApiTools.delete({ id: this.selectedTool.id })
      this.$q.notify({
        position: 'top',
        message: 'API Tool has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.$router?.push('/api-tools')
    },
    save() {
      this.loading = true
      this.$store.dispatch('saveApiTool')
      this.loading = false
    },
    async clone() {
      //const res = await this.create(this.selectedTool)
      const newTool = _.cloneDeep(this.selectedTool)
      delete newTool._metadata
      delete newTool.id
      newTool.system_name = newTool.system_name + '_COPY'
      let i = 2
      while (this.items.some((item) => item.system_name === newTool.system_name)) {
        i++
        newTool.system_name = `${this.selectedTool.system_name}_COPY_${i}`
      }
      this.clonedTool = newTool
      this.showCloneDialog = true
    },
  },
}
</script>
