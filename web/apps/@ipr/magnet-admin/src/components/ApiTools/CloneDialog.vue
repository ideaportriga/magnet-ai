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
import { ref } from 'vue'
import { useChroma } from '@shared'
export default {
  props: ['show', 'tool'],
  emits: ['cancel'],
  setup() {
    const newTool = ref(null)
    const loading = ref(false)
    const { items, create } = useChroma('api_tools')
    return { newTool, loading, items, create }
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
        const res = await this.create(JSON.stringify(this.newTool))
        if (res.ok) {
          const data = await res.json()
          this.$router?.push(`/api-tools/${data?.id}`)
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
