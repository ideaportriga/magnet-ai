<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 Settings
.col
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='loading')
q-inner-loading(:showing='loading')
</template>

<script setup>
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'vuex'

const store = useStore()
const $q = useQuasar()
const loading = ref(false)

const validateSettings = () => {
  const settings = store.getters.noteTakerSettings || {}
  if (settings.create_knowledge_graph_embedding && !settings.knowledge_graph_system_name) {
    $q.notify({
      position: 'top',
      message: 'Select a knowledge graph when embedding is enabled.',
      color: 'positive',
      textColor: 'black',
      timeout: 1200,
    })
    return false
  }

  const checks = [
    { enabled: settings.chapters?.enabled, template: settings.chapters?.prompt_template, label: 'chapters' },
    { enabled: settings.summary?.enabled, template: settings.summary?.prompt_template, label: 'summary' },
    { enabled: settings.insights?.enabled, template: settings.insights?.prompt_template, label: 'insights' },
  ]

  const missing = checks.find((item) => item.enabled && !item.template)
  if (!missing) return true

  $q.notify({
    position: 'top',
    message: `Select a prompt template for ${missing.label}.`,
    color: 'positive',
    textColor: 'black',
    timeout: 1200,
  })
  return false
}

const save = async () => {
  if (!validateSettings()) return
  loading.value = true
  try {
    await store.dispatch('saveNoteTakerSettings')
    $q.notify({
      position: 'top',
      message: 'Note Taker settings saved successfully',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } catch (error) {
    $q.notify({
      position: 'top',
      message: error?.message || 'Failed to save Note Taker settings',
      color: 'positive',
      textColor: 'black',
      timeout: 1000,
    })
  } finally {
    loading.value = false
  }
}
</script>
