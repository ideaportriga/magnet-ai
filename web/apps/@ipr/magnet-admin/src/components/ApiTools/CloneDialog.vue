<template lang="pug">
km-popup-confirm(
  :visible='show',
  title='Clone Assistant Tool',
  confirmButtonLabel='Clone',
  cancelButtonLabel='Cancel',
  @confirm='cloneTool',
  @cancel='$emit("cancel")',
  :loading='loading',
  v-if='newTool'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Name
  .full-width.q-mb-md
    km-input(v-model='newTool.name')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 Description
  .full-width.q-mb-md
    km-input(v-model='newTool.description', type='textarea', rows='5')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 System name
  .full-width.q-mb-md
    km-input(v-model='newTool.system_name', :rules='[uniqueSystemName]', ref='systemNameInput')
</template>
<script>
import { ref, computed } from 'vue'
import { useEntityQueries } from '@/queries/entities'
export default {
  props: ['show', 'tool'],
  emits: ['cancel'],
  setup() {
    const newTool = ref(null)
    const loading = ref(false)
    const queries = useEntityQueries()
    const { data: apiToolsListData } = queries.api_tools.useList()
    const { mutateAsync: createApiTool } = queries.api_tools.useCreate()
    return { newTool, loading, apiToolsListData, createApiTool }
  },
  computed: {
    items() {
      return this.apiToolsListData?.items ?? []
    },
  },
  watch: {
    tool(newVal) {
      this.newTool = newVal
    },
  },
  methods: {
    async cloneTool() {
      this.loading = true

      const systemName = this.$refs.systemNameInput.validate()
      if (systemName) {
        const data = await this.createApiTool(this.newTool)
        if (data?.id) {
          this.$router?.push(`/api-tools/${data.id}`)
          this.$emit('cancel')
        }
      }
      this.loading = false
    },
    uniqueSystemName(value) {
      if (this.items.some((item) => item.system_name === value)) {
        return 'System name already exists'
      }
      return false
    },
  },
}
</script>
