<template lang="pug">
    .col-auto.q-py-auto
      .km-heading-4 {{ server?.name }}
    .col
    .col-auto.q-mr-sm
      km-btn(label='Record info', icon='info', iconSize='16px') 
      q-tooltip.bg-white.block-shadow
        .q-pa-sm
          .q-mb-sm
            .text-secondary-text.km-button-xs-text Created:
            .text-secondary-text.km-description {{ info.created_at }}
          div
            .text-secondary-text.km-button-xs-text Modified:
            .text-secondary-text.km-description {{ info.updated_at }}
    q-separator(vertical, color='white')
    .col-auto.text-white.q-mx-md
      km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')  
    .col-auto.text-white.q-mr-md
      q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
        q-menu(anchor='bottom right', self='top right')
          q-item(clickable, @click='showDeleteDialog = true', dense)
            q-item-section
              .km-heading-3 Delete
    q-inner-loading(:showing='loading')
    km-popup-confirm(
      :visible='showDeleteDialog',
      confirmButtonLabel='Ok, delete',
      cancelButtonLabel='Cancel',
      notificationIcon='fas fa-triangle-exclamation',
      @confirm='deleteServer',
      @cancel='showDeleteDialog = false'
    )
      .row.item-center.justify-center.km-heading-7 You are about to delete a Model Provider
      .row.text-center.justify-center This action will delete all Models added under this Model Provider. All affected Prompt Templates will stop working unless you change their model to a working one.
    
    </template>
    <script setup>
    import { ref, computed } from 'vue'
    import { useStore } from 'vuex'
    import { useChroma } from '@shared'
    import { useQuasar } from 'quasar'
    import { useRouter } from 'vue-router'
    import { formatDateTime } from '@shared/utils/dateTime'
    
    const store = useStore()
    const q = useQuasar()
    const router = useRouter()
    const showDeleteDialog = ref(false)
    const loading = ref(false)
    
    const server = computed(() => store.getters.model_provider)
    
    const info = computed(() => {
      return {
        created_at: formatDateTime(server.value?.created_at),
        updated_at: formatDateTime(server.value?.updated_at),
      }
    })
    
    const save = async () => {
      loading.value = true
      // await store.dispatch('saveMcpServer')
      loading.value = false
    }
    const deleteServer = async () => {
      // await deleteMcpServer({ id: store.getters.mcp_server.id })
      q.notify({
        position: 'top',
        message: 'Model Provider has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      // store.dispatch('setMcpServer', null)
      showDeleteDialog.value = false
      router.push('/model-providers')
    }
    </script>
    