<template lang="pug">
.q-gutter-md
  //- ── Salesforce ────────────────────────────────────────────────────
  .km-heading-8 Salesforce
  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Send transcript to Salesforce
      q-toggle(v-model='sendTranscriptToSalesforce', color='primary')
    .km-description.text-secondary-text.q-pt-2 Push completed transcripts to Salesforce.

  .q-gutter-md(v-if='sendTranscriptToSalesforce')
    .km-field
      .text-secondary-text.q-pb-xs API Server
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='salesforceApiServer',
            :options='apiServers',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, height='30px', clearable
          )
        .col-auto(v-if='salesforceApiServer')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToApiServer(salesforceApiServer)')
      .km-description.text-secondary-text.q-pt-2 API server for Salesforce tool calls.

    .km-field
      .text-secondary-text.q-pb-xs STT Recording Tool
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='salesforceSttRecordingTool',
            :options='salesforceAvailableTools',
            option-label='label',
            option-value='value',
            emit-value, map-options, height='30px', clearable
          )
        .col-auto(v-if='salesforceSttRecordingTool')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToTool(salesforceApiServer, salesforceSttRecordingTool)')
      .km-description.text-secondary-text.q-pt-2 Tool for creating STT recordings in Salesforce.

  q-separator

  //- ── Confluence ────────────────────────────────────────────────────
  .km-heading-8 Confluence
  .km-field
    .row.items-center.justify-between
      .text-secondary-text.q-pb-xs.km-title Publish meeting notes to Confluence
      q-toggle(v-model='confluenceEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-2 Create a Confluence page containing the generated Summary and Chapters.

  .q-gutter-md(v-if='confluenceEnabled')
    .km-field
      .text-secondary-text.q-pb-xs API Server
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='confluenceApiServer',
            :options='apiServers',
            option-label='name',
            option-value='system_name',
            emit-value, map-options, height='30px', clearable
          )
        .col-auto(v-if='confluenceApiServer')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToApiServer(confluenceApiServer)')
      .km-description.text-secondary-text.q-pt-2 API server used to call Confluence tools.

    .km-field
      .text-secondary-text.q-pb-xs Create Page Tool
      .row.items-center.q-gutter-sm
        .col
          km-select(
            v-model='confluenceCreatePageTool',
            :options='confluenceAvailableTools',
            option-label='label',
            option-value='value',
            emit-value, map-options, height='30px', clearable
          )
        .col-auto(v-if='confluenceCreatePageTool')
          km-btn(icon='open_in_new', flat, dense, @click='navigateToTool(confluenceApiServer, confluenceCreatePageTool)')
      .km-description.text-secondary-text.q-pt-2 API tool used to create the Confluence page.

    .km-field
      .text-secondary-text.q-pb-xs Space ID
      km-input-flat.full-width(
        placeholder='e.g. 10387460',
        :modelValue='confluenceSpaceKey',
        @input='confluenceSpaceKey = $event'
      )
      .km-description.text-secondary-text.q-pt-2 Confluence REST v2 spaceId where the page will be created.

    .km-field
      .text-secondary-text.q-pb-xs Parent Page ID (optional)
      km-input-flat.full-width(
        placeholder='e.g. 123456',
        :modelValue='confluenceParentId',
        @input='confluenceParentId = $event'
      )
      .km-description.text-secondary-text.q-pt-2 If set, the page will be created under the specified parent.

    .km-field
      .text-secondary-text.q-pb-xs Title Template
      km-input-flat.full-width(
        placeholder='Meeting notes: {meeting_title} ({date})',
        :modelValue='confluenceTitleTemplate',
        @input='confluenceTitleTemplate = $event'
      )
      .km-description.text-secondary-text.q-pt-2 Available placeholders: {meeting_title}, {date}, {job_id}, {meeting_id}.
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

const apiServers = computed(() => store.getters['chroma/api_servers']?.items || [])

const setting = (path: string, fallback: any = false) => computed({
  get: () => path.split('.').reduce((o: any, k) => o?.[k], store.getters.noteTakerSettings) ?? fallback,
  set: (v: any) => store.dispatch('updateNoteTakerSetting', { path, value: v }),
})

const sendTranscriptToSalesforce = setting('integration.salesforce.send_transcript_to_salesforce')
const salesforceApiServer = setting('integration.salesforce.salesforce_api_server', '')
const salesforceSttRecordingTool = setting('integration.salesforce.salesforce_stt_recording_tool', '')
const confluenceEnabled = setting('integration.confluence.enabled')
const confluenceApiServer = setting('integration.confluence.confluence_api_server', '')
const confluenceCreatePageTool = setting('integration.confluence.confluence_create_page_tool', '')
const confluenceSpaceKey = setting('integration.confluence.space_key', '')
const confluenceParentId = setting('integration.confluence.parent_id', '')
const confluenceTitleTemplate = setting('integration.confluence.title_template', '')

const salesforceAvailableTools = computed(() => {
  const name = salesforceApiServer.value
  if (!name) return []
  const server = apiServers.value.find((s: any) => s.system_name === name)
  return server?.tools?.map((t: any) => ({ label: t.name, value: t.system_name })) || []
})

const confluenceAvailableTools = computed(() => {
  const name = confluenceApiServer.value
  if (!name) return []
  const server = apiServers.value.find((s: any) => s.system_name === name)
  return server?.tools?.map((t: any) => ({ label: t.name, value: t.system_name })) || []
})

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) window.open(router.resolve({ path: `/api-servers/${server.id}` }).href, '_blank')
}
const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) window.open(router.resolve({ path: `/api-servers/${server.id}/tools/${toolName}` }).href, '_blank')
}
</script>
