<template>
  <km-popup-confirm v-if="newTool" :visible="show" :title="m.dialog_cloneApiTool()" :confirm-button-label="m.common_clone()" :cancel-button-label="m.common_cancel()" :loading="loading" @confirm="cloneTool" @cancel="$emit(&quot;cancel&quot;)">
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_name() }}</div>
    <div class="full-width mb-md">
      <km-input v-model="newTool.name" />
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_description() }}</div>
    <div class="full-width mb-md">
      <km-input v-model="newTool.description" type="textarea" rows="5" />
    </div>
    <div class="km-field text-secondary-text pb-xs pl-sm">{{ m.common_systemName() }}</div>
    <div class="full-width mb-md">
      <km-input ref="systemNameInput" v-model="newTool.system_name" :rules="[uniqueSystemName]" />
    </div>
  </km-popup-confirm>
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
