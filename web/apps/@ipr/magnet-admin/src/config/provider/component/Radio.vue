<template lang="pug">
q-radio(:model-value='row?.is_default', :val='true', @click.stop='onRadioClick')
</template>
<script>
import { defineComponent } from 'vue'
import { fetchData } from '@shared'
import { useAppStore } from '@/stores/appStore'
import { useQueryClient } from '@tanstack/vue-query'

export default defineComponent({
  props: ['row', 'name'],

  setup() {
    const appStore = useAppStore()
    const queryClient = useQueryClient()
    return { appStore, queryClient }
  },

  methods: {
    async onRadioClick() {
      const endpoint = this.appStore.config?.model?.endpoint
      const service = this.appStore.config?.model?.service || ''
      const credentials = this.appStore.config?.model?.credentials

      await fetchData({
        method: 'POST',
        endpoint,
        service: `${service}/set_default`,
        credentials,
        body: JSON.stringify({
          type: this.row?.type,
          system_name: this.row?.system_name,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      await this.queryClient.invalidateQueries({ queryKey: ['model'] })
    },
  },
})
</script>
