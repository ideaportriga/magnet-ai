<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 Settings
.col
.col-auto.text-white.q-mx-md
  .row.items-center.q-gap-8.no-wrap
    km-btn(
      label='Reload Runtime',
      icon='restart_alt', iconSize='16px',
      flat, bg='background',
      @click='reloadRuntime',
      :loading='reloading',
      :disable='!activeRecordId'
    )
    km-btn(
      label='Save',
      icon='far fa-save', iconSize='16px',
      color='primary', bg='background',
      @click='save',
      :loading='loading'
    )
    q-btn(flat, round, dense, icon='more_vert')
      q-menu
        q-list(dense, style='min-width: 140px')
          q-item(clickable, v-close-popup, @click='showDeleteConfirm = true', :disable='!activeRecordId')
            q-item-section(avatar)
              q-icon(name='delete', color='negative', size='sm')
            q-item-section Delete

q-dialog(v-model='showDeleteConfirm', persistent)
  q-card(style='min-width: 360px')
    q-card-section
      .text-h6 Delete Note Taker Settings
    q-card-section.q-pt-none
      | Are you sure you want to delete "{{ activeRecordName }}"? This action cannot be undone.
    q-card-actions(align='right')
      q-btn(flat, label='Cancel', v-close-popup)
      q-btn(flat, label='Delete', color='negative', @click='confirmDelete', :loading='deleting')

q-inner-loading(:showing='loading || deleting')
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()
const $q = useQuasar()
const loading = ref(false)
const reloading = ref(false)
const deleting = ref(false)
const showDeleteConfirm = ref(false)

const activeRecord = computed(() => store.getters.noteTakerSettingsActiveRecord)
const activeRecordId = computed(() => activeRecord.value?.id || activeRecord.value?.system_name)
const activeRecordName = computed(() => activeRecord.value?.name || activeRecordId.value || '')

const validateSettings = () => {
  const settings = store.getters.noteTakerSettings || {}
  if (settings.create_knowledge_graph_embedding && !settings.knowledge_graph_system_name) {
    $q.notify({ position: 'top', message: 'Select a knowledge graph when embedding is enabled.', color: 'positive', textColor: 'black', timeout: 1200 })
    return false
  }
  if (settings.integration?.salesforce?.send_transcript_to_salesforce) {
    if (!settings.integration?.salesforce?.salesforce_api_server || !settings.integration?.salesforce?.salesforce_stt_recording_tool) {
      $q.notify({ position: 'top', message: 'Select Salesforce API server and STT recording tool.', color: 'positive', textColor: 'black', timeout: 1200 })
      return false
    }
  }
  const checks = [
    { enabled: settings.chapters?.enabled, template: settings.chapters?.prompt_template, label: 'chapters' },
    { enabled: settings.summary?.enabled, template: settings.summary?.prompt_template, label: 'summary' },
    { enabled: settings.insights?.enabled, template: settings.insights?.prompt_template, label: 'insights' },
  ]
  const missing = checks.find((item) => item.enabled && !item.template)
  if (missing) {
    $q.notify({ position: 'top', message: `Select a prompt template for ${missing.label}.`, color: 'positive', textColor: 'black', timeout: 1200 })
    return false
  }
  return true
}

const save = async () => {
  if (!validateSettings()) return
  loading.value = true
  try {
    await store.dispatch('saveNoteTakerSettings')
    $q.notify({ position: 'top', message: 'Note Taker settings saved successfully', color: 'positive', textColor: 'black', timeout: 1000 })
  } catch (error: any) {
    $q.notify({ position: 'top', message: error?.message || 'Failed to save', color: 'negative', textColor: 'white', timeout: 2000 })
  } finally { loading.value = false }
}

const reloadRuntime = async () => {
  if (!activeRecordId.value) return
  reloading.value = true
  try {
    await store.dispatch('reloadNoteTakerRuntime', activeRecordId.value)
    $q.notify({ position: 'top', message: 'Runtime reloaded successfully', color: 'positive', textColor: 'black', timeout: 1000 })
  } catch (error: any) {
    $q.notify({ position: 'top', message: error?.message || 'Failed to reload runtime', color: 'negative', textColor: 'white', timeout: 2000 })
  } finally { reloading.value = false }
}

const confirmDelete = async () => {
  if (!activeRecordId.value) return
  deleting.value = true
  try {
    await store.dispatch('deleteNoteTakerSettings', activeRecordId.value)
    showDeleteConfirm.value = false
    $q.notify({ position: 'top', message: 'Note Taker settings deleted', color: 'positive', textColor: 'black', timeout: 1000 })
    router.push('/note-taker')
  } catch (error: any) {
    $q.notify({ position: 'top', message: error?.message || 'Failed to delete', color: 'negative', textColor: 'white', timeout: 2000 })
  } finally { deleting.value = false }
}
</script>
