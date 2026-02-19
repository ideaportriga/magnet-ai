<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRecord?.name || 'Settings' }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px')
  q-tooltip.bg-white.block-shadow
    .q-pa-sm
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created:
        .text-secondary-text.km-description {{ info.created_at }}
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ info.updated_at }}
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created by:
        .text-secondary-text.km-description {{ info.created_by }}
      div
        .text-secondary-text.km-button-xs-text Modified by:
        .text-secondary-text.km-description {{ info.updated_by }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Start Run', icon='play_arrow', iconSize='16px', @click='showRunDialog = true')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='loading')
q-inner-loading(:showing='loading')
note-taker-start-run-dialog(v-model='showRunDialog', :config-name='activeRecord?.name')
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'vuex'
import { formatDateTime } from '@shared/utils/dateTime'
import NoteTakerStartRunDialog from './StartRunDialog.vue'

const store = useStore()
const $q = useQuasar()
const loading = ref(false)
const showRunDialog = ref(false)

const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)

const info = computed(() => {
  const rec = activeRecord.value
  return {
    created_at: rec?.created_at ? formatDateTime(rec.created_at) : '—',
    updated_at: rec?.updated_at ? formatDateTime(rec.updated_at) : '—',
    created_by: rec?.created_by ? String(rec.created_by) : 'Unknown',
    updated_by: rec?.updated_by ? String(rec.updated_by) : 'Unknown',
  }
})

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

  if (settings.integration?.salesforce?.send_transcript_to_salesforce) {
    if (
      !settings.integration?.salesforce?.salesforce_api_server ||
      !settings.integration?.salesforce?.salesforce_stt_recording_tool
    ) {
      $q.notify({
        position: 'top',
        message: 'Select Salesforce API server and STT recording tool.',
        color: 'positive',
        textColor: 'black',
        timeout: 1200,
      })
      return false
    }
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
