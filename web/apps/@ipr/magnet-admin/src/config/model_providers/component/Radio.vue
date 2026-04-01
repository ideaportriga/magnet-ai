<template lang="pug">
q-radio(:model-value='row?.is_default', :val='true', @click.stop='showDialog = true')

km-popup-confirm(
  :visible='showDialog',
  confirmButtonLabel='OK, change default',
  notificationIcon='fas fa-circle-info',
  cancelButtonLabel='Cancel',
  @cancel='showDialog = false',
  @confirm='onRadioClick'
)
  .row.item-center.justify-center.km-heading-7 You are about to change default model
  .row.text-center.justify-center This will affect newly created Prompt Templates and any existing
  .row.text-center.justify-center Prompt Templates that have no model selected.
</template>
<script>
import { defineComponent, ref } from 'vue'
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
  data() {
    return {
      showDialog: ref(false),
    }
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
      this.showDialog = false
    },
  },
})
</script>
