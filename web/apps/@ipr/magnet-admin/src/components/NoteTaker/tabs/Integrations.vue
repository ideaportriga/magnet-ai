<template lang="pug">
div
  km-section(title='Salesforce', subTitle='Send Note Taker transcripts to a Salesforce org')
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Send Transcript to Salesforce
      q-toggle(v-model='sendTranscriptToSalesforce', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Push completed transcripts to Salesforce

    .q-gutter-md.q-mt-md(v-if='sendTranscriptToSalesforce')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Server
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='salesforceApiServer',
              :options='apiServers',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, height='auto', minHeight='36px', clearable
            )
          .col-auto(v-if='salesforceApiServer')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToApiServer(salesforceApiServer)')
        .km-description.text-secondary-text.q-pt-xs.q-pl-8 API server for Salesforce tool calls.

      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 STT Recording Tool
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='salesforceSttRecordingTool',
              :options='salesforceAvailableTools',
              option-label='label',
              option-value='value',
              emit-value, map-options, height='auto', minHeight='36px', clearable
            )
          .col-auto(v-if='salesforceSttRecordingTool')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToTool(salesforceApiServer, salesforceSttRecordingTool)')
        .km-description.text-secondary-text.q-pt-xs.q-pl-8 Tool for creating STT recordings in Salesforce.

  q-separator.q-my-lg

  km-section(title='Confluence', subTitle='Publish Note Taker output to a Confluence space')
    .row.items-center.justify-between
      .km-field.text-secondary-text.q-pl-8 Publish Transcript Summary to Confluence
      q-toggle(v-model='confluenceEnabled', color='primary')
    .km-description.text-secondary-text.q-pt-xs.q-pl-8 Push completed summaries to Confluence

    .q-gutter-md.q-mt-md(v-if='confluenceEnabled')
      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Server
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='confluenceApiServer',
              :options='apiServers',
              option-label='name',
              option-value='system_name',
              emit-value, map-options, height='auto', minHeight='36px', clearable
            )
          .col-auto(v-if='confluenceApiServer')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToApiServer(confluenceApiServer)')

      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Create Page Tool
        .row.items-center.q-gutter-sm
          .col
            km-select(
              v-model='confluenceCreatePageTool',
              :options='confluenceAvailableTools',
              option-label='label',
              option-value='value',
              emit-value, map-options, height='auto', minHeight='36px', clearable
            )
          .col-auto(v-if='confluenceCreatePageTool')
            km-btn(icon='open_in_new', flat, dense, @click='navigateToTool(confluenceApiServer, confluenceCreatePageTool)')

      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Space ID
        km-input.full-width(
          v-model='confluenceSpaceKey',
          placeholder='e.g. 10387460',
          height='30px'
        )

      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Parent Page ID (optional)
        km-input.full-width(
          v-model='confluenceParentId',
          placeholder='e.g. 123456',
          height='30px'
        )

      div
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 Title Template
        km-input.full-width(
          v-model='confluenceTitleTemplate',
          placeholder='Meeting notes: {meeting_title} ({date})',
          height='30px'
        )
        .km-description.text-secondary-text.q-pt-xs.q-pl-8 Available placeholders: {meeting_title}, {date}, {job_id}, {meeting_id}.
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNoteTakerStore } from '@/stores/noteTakerStore'
import { useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'

const ntStore = useNoteTakerStore()
const router = useRouter()
const queries = useEntityQueries()

const { data: apiServersListData } = queries.api_servers.useList()
const apiServers = computed(() => apiServersListData.value?.items || [])

const setting = (path: string, fallback: any = false) => computed({
  get: () => path.split('.').reduce((o: any, k) => o?.[k], ntStore.settings) ?? fallback,
  set: (v: any) => ntStore.updateSetting( { path, value: v }),
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
