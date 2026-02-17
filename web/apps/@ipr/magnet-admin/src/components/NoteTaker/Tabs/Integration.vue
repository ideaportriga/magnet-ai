<template lang="pug">
.full-width

  km-section(
    title='Send transcript to Salesforce',
    subTitle='Push completed transcripts to Salesforce.'
  )
    .column.q-gap-16
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='sendTranscriptToSalesforce', color='primary', dense)
        .col Send transcript to Salesforce
      .column.q-pl-8.q-gap-12(v-if='sendTranscriptToSalesforce')
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Server
          .row.items-center.q-gap-16.no-wrap
            .col(style='max-width: 320px')
              km-select(
                v-model='salesforceApiServer',
                :options='apiServers',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                height='30px',
                clearable,
                placeholder='Select API server'
              )
            .col-auto(v-if='salesforceApiServer')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToApiServer(salesforceApiServer)'
              )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 API server for Salesforce tool calls.
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 STT Recording Tool
          .row.items-center.q-gap-16.no-wrap
            .col(style='max-width: 320px')
              km-select(
                v-model='salesforceSttRecordingTool',
                :options='availableTools',
                option-label='label',
                option-value='value',
                emit-value,
                map-options,
                height='30px',
                clearable,
                placeholder='Select STT recording tool'
              )
            .col-auto(v-if='salesforceSttRecordingTool')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToTool(salesforceApiServer, salesforceSttRecordingTool)'
              )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 Tool for creating STT recordings in Salesforce.

  q-separator.q-my-lg

  km-section(
    title='Publish meeting notes to Confluence',
    subTitle='Create a Confluence page containing the generated Summary and Chapters.'
  )
    .column.q-gap-16
      .row.items-baseline
        .col-auto.q-mr-sm
          q-toggle(v-model='confluenceEnabled', color='primary', dense)
        .col Publish meeting notes to Confluence
      .column.q-pl-8.q-gap-12(v-if='confluenceEnabled')
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 API Server
          .row.items-center.q-gap-16.no-wrap
            .col(style='max-width: 320px')
              km-select(
                v-model='confluenceApiServer',
                :options='apiServers',
                option-label='name',
                option-value='system_name',
                emit-value,
                map-options,
                height='30px',
                clearable,
                placeholder='Select API server'
              )
            .col-auto(v-if='confluenceApiServer')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToApiServer(confluenceApiServer)'
              )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 API server used to call Confluence tools.
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Create Page Tool
          .row.items-center.q-gap-16.no-wrap
            .col(style='max-width: 320px')
              km-select(
                v-model='confluenceCreatePageTool',
                :options='confluenceAvailableApiTools',
                option-label='label',
                option-value='value',
                emit-value,
                map-options,
                height='30px',
                clearable,
                placeholder='Select create page tool'
              )
            .col-auto(v-if='confluenceCreatePageTool')
              km-btn(
                icon='open_in_new',
                flat,
                dense,
                @click='navigateToTool(confluenceApiServer, confluenceCreatePageTool)'
              )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 API tool used to create the Confluence page.
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Space ID
          .row.items-center.q-gap-16.no-wrap
            km-input-flat.full-width(
              placeholder='e.g. 10387460',
              :modelValue='confluenceSpaceKey',
              @input='confluenceSpaceKey = $event'
            )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 Confluence REST v2 spaceId where the page will be created.
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Parent Page ID (optional)
          .row.items-center.q-gap-16.no-wrap
            km-input-flat.full-width(
              placeholder='e.g. 123456',
              :modelValue='confluenceParentId',
              @input='confluenceParentId = $event'
            )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 If set, the page will be created under the specified parent.
        .column
          .km-field.text-secondary-text.q-pb-xs.q-pl-8 Title Template
          .row.items-center.q-gap-16.no-wrap
            km-input-flat.full-width(
              placeholder='Meeting notes: {meeting_title} ({date})',
              :modelValue='confluenceTitleTemplate',
              @input='confluenceTitleTemplate = $event'
            )
          .km-description.text-secondary-text.q-mt-xs.q-pl-8 Available placeholders: {meeting_title}, {date}, {job_id}, {meeting_id}.
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()

const apiServers = computed(() => {
  return store.getters['chroma/api_servers']?.items || []
})

const sendTranscriptToSalesforce = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.send_transcript_to_salesforce ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.send_transcript_to_salesforce', value })
  },
})

const salesforceApiServer = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.salesforce_api_server || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.salesforce_api_server', value })
  },
})

const salesforceSttRecordingTool = computed({
  get: () => store.getters.noteTakerSettings?.integration?.salesforce?.salesforce_stt_recording_tool || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.salesforce.salesforce_stt_recording_tool', value })
  },
})

const availableTools = computed(() => {
  const serverName = salesforceApiServer.value
  if (!serverName) return []
  const server = apiServers.value.find((s: any) => s.system_name === serverName)
  return server?.tools?.map((t: any) => ({
    label: t.name,
    value: t.system_name,
  })) || []
})

const confluenceEnabled = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.enabled ?? false,
  set: (value: boolean) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.enabled', value })
  },
})

const confluenceApiServer = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.confluence_api_server || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.confluence_api_server', value })
  },
})

const confluenceCreatePageTool = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.confluence_create_page_tool || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.confluence_create_page_tool', value })
  },
})

const confluenceSpaceKey = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.space_key || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.space_key', value })
  },
})

const confluenceParentId = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.parent_id || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.parent_id', value })
  },
})

const confluenceTitleTemplate = computed({
  get: () => store.getters.noteTakerSettings?.integration?.confluence?.title_template || '',
  set: (value: string) => {
    store.dispatch('updateNoteTakerSetting', { path: 'integration.confluence.title_template', value })
  },
})

const confluenceAvailableApiTools = computed(() => {
  const serverName = confluenceApiServer.value
  if (!serverName) return []
  const server = apiServers.value.find((s: any) => s.system_name === serverName)
  return server?.tools?.map((t: any) => ({
    label: t.name,
    value: t.system_name,
  })) || []
})

const navigateToApiServer = (systemName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === systemName)
  if (server) {
    window.open(router.resolve({ path: `/api-servers/${server.id}` }).href, '_blank')
  }
}

const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) {
    window.open(
      router.resolve({ path: `/api-servers/${server.id}/tools/${toolName}` }).href,
      '_blank'
    )
  }
}
</script>
