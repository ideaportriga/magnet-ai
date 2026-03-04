<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ configName }}
.col
.col-auto.text-white.q-mx-md
  km-btn(label='Execute', icon='play_arrow', iconSize='16px', color='primary', bg='background', @click='openExecuteDrawer')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='saving', :disable='saving')
.col-auto.text-white.q-mr-md
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'

const store = useStore()
const route = useRoute()
const $q = useQuasar()

const configId = computed(() => route.params.id)
const config = computed(() => store.getters.selectedPromptQueueConfig)
const configName = computed(() => config.value?.name ?? '')
const saving = computed(() => store.getters.promptQueueLoading ?? false)

const openExecuteDrawer = () => {
  store.commit('setExecuteDrawerOpen', true)
}

const save = async () => {
  const cfg = config.value
  if (!cfg || !configId.value) return

  try {
    await store.dispatch('updatePromptQueueConfig', {
      configId: configId.value,
      updates: {
        name: cfg.name,
        description: cfg.description,
        system_name: cfg.system_name,
        config: cfg.config,
      },
    })
    $q.notify({
      position: 'top',
      message: 'Prompt Queue Config saved',
      color: 'positive',
      timeout: 1000,
    })
  } catch (error) {
    $q.notify({
      position: 'top',
      message: error?.message || 'Failed to save',
      color: 'negative',
      timeout: 2000,
    })
  }
}
</script>
