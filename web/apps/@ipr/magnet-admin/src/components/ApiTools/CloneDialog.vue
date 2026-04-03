<template lang="pug">
km-popup-confirm(
  :visible='show',
  title='Clone API Tool',
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
import { useEntityDetail } from '@/composables/useEntityDetail'
export default {
  props: ['show', 'tool'],
  emits: ['cancel'],
  setup() {
    const newTool = ref(null)
    const loading = ref(false)
    const { draft, updateField, save: saveServer } = useEntityDetail('api_servers')
    return { newTool, loading, draft, updateField, saveServer }
  },
  computed: {
    items() {
      return this.draft?.tools ?? []
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
      try {
        const systemName = this.$refs.systemNameInput.validate()
        if (systemName) {
          const tools = [...(this.draft?.tools || []), this.newTool]
          this.updateField('tools', tools)
          const result = await this.saveServer()
          if (result.success) {
            this.$router?.push(`/api-servers/${this.$route.params.id}/tools/${this.newTool.system_name}`)
            this.$emit('cancel')
          }
        }
      } finally {
        this.loading = false
      }
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
