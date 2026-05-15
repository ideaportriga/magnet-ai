<template>
  <div>
    <km-section title="Salesforce" sub-title="Send Note Taker transcripts to a Salesforce org">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Send Transcript to Salesforce</div>
        <km-toggle v-model="sendTranscriptToSalesforce" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Push completed transcripts to Salesforce</div>
      <div v-if="sendTranscriptToSalesforce" class="stack mt-md" data-gap="md">
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">API Server</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="salesforceApiServer" :options="apiServers" option-label="name" option-value="system_name" emit-value map-options height="auto" min-height="36px" clearable />
            </div>
            <div v-if="salesforceApiServer" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToApiServer(salesforceApiServer)" />
            </div>
          </div>
          <div class="km-description text-secondary-text pt-xs pl-sm">API server for Salesforce tool calls.</div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">STT Recording Tool</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="salesforceSttRecordingTool" :options="salesforceAvailableTools" option-label="label" option-value="value" emit-value map-options height="auto" min-height="36px" clearable />
            </div>
            <div v-if="salesforceSttRecordingTool" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToTool(salesforceApiServer, salesforceSttRecordingTool)" />
            </div>
          </div>
          <div class="km-description text-secondary-text pt-xs pl-sm">Tool for creating STT recordings in Salesforce.</div>
        </div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Confluence" sub-title="Publish Note Taker output to a Confluence space">
      <div class="cluster" data-justify="between">
        <div class="km-field text-secondary-text pl-sm">Publish Transcript Summary to Confluence</div>
        <km-toggle v-model="confluenceEnabled" />
      </div>
      <div class="km-description text-secondary-text pt-xs pl-sm">Push completed summaries to Confluence</div>
      <div v-if="confluenceEnabled" class="stack mt-md" data-gap="md">
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">API Server</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="confluenceApiServer" :options="apiServers" option-label="name" option-value="system_name" emit-value map-options height="auto" min-height="36px" clearable />
            </div>
            <div v-if="confluenceApiServer" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToApiServer(confluenceApiServer)" />
            </div>
          </div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Create Page Tool</div>
          <div class="cluster" data-gap="sm">
            <div class="flex-1">
              <km-select v-model="confluenceCreatePageTool" :options="confluenceAvailableTools" option-label="label" option-value="value" emit-value map-options height="auto" min-height="36px" clearable />
            </div>
            <div v-if="confluenceCreatePageTool" class="flex-none">
              <km-btn icon="external-link" flat dense @click="navigateToTool(confluenceApiServer, confluenceCreatePageTool)" />
            </div>
          </div>
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Space ID</div>
          <km-input v-model="confluenceSpaceKey" class="full-width" :placeholder="m.noteTaker_exampleLinearTeamId()" height="30px" />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Parent Page ID (optional)</div>
          <km-input v-model="confluenceParentId" class="full-width" :placeholder="m.noteTaker_exampleLinearProjectId()" height="30px" />
        </div>
        <div>
          <div class="km-field text-secondary-text pb-xs pl-sm">Title Template</div>
          <km-input v-model="confluenceTitleTemplate" class="full-width" :placeholder="m.noteTaker_meetingNotesTemplate()" height="30px" />
          <div class="km-description text-secondary-text pt-xs pl-sm">Available placeholders: {meeting_title}, {date}, {job_id}, {meeting_id}.</div>
        </div>
      </div>
    </km-section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'
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
  if (server) router.push(`/api-servers/${server.id}`)
}
const navigateToTool = (serverSystemName: string, toolName: string) => {
  const server = apiServers.value.find((s: any) => s.system_name === serverSystemName)
  if (server) router.push(`/api-servers/${server.id}/tools/${toolName}`)
}
</script>
