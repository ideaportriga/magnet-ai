<template lang="pug">
km-popup-confirm(
  :visible='show',
  :title='m.dialog_cloneApiTool()',
  :confirmButtonLabel='m.common_clone()',
  :cancelButtonLabel='m.common_cancel()',
  @confirm='cloneTool',
  @cancel='$emit("cancel")',
  :loading='loading',
  v-if='newTool'
)
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_name() }}
  .full-width.q-mb-md
    km-input(v-model='newTool.name')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_description() }}
  .full-width.q-mb-md
    km-input(v-model='newTool.description', type='textarea', rows='5')
  .km-field.text-secondary-text.q-pb-xs.q-pl-8 {{ m.common_systemName() }}
  .full-width.q-mb-md
    km-input(v-model='newTool.system_name', :rules='[uniqueSystemName]', ref='systemNameInput')
</template>
<script>
import { ref } from 'vue'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
export default {
  props: ['show', 'tool'],
  emits: ['cancel'],
  setup() {
    const newTool = ref(null)
    const loading = ref(false)
    const { draft, updateField, save: saveServer } = useEntityDetail('api_servers')
    return { m, newTool, loading, draft, updateField, saveServer }
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
        return m.validation_systemNameAlreadyExists()
      }
      return false
    },
  },
}
</script>
