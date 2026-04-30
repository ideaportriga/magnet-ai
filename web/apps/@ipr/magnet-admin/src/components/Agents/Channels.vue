<template>
  <div class="mr-sm">
    <km-section :title="m.section_web()" :sub-title="m.subtitle_web()">
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
        <km-toggle v-model="enable_iframe" size="sm" :disable="false" />
      </div>
      <template v-if="enable_iframe">
        <km-separator />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Theme</div>
        <div class="cluster" data-gap="lg" data-wrap="no" style="inline-size: 220px">
          <km-select v-model="theme" :options="themeOptions" size="sm" :disable="false" style="inline-size: 220px" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
          Show Close button
          <km-toggle v-model="show_close_button" size="sm" :disable="false" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
          Show Logo
          <km-toggle v-model="isIconHide" size="sm" :disable="false" />
        </div>
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">URL</div>
        <div class="cluster">
          <div class="flex-1 mr-sm">
            <km-input ref="input" border-radius="8px" height="36px" :readonly="true" :model-value="appUrl" />
          </div>
          <div class="flex-none">
            <km-btn icon="copy" icon-size="16px" size="sm" flat tooltip="Copy" @click="copy" />
          </div>
          <div class="flex-none">
            <km-btn icon="external-link" icon-size="16px" size="sm" flat tooltip="Open in new tab" @click="openInNewTab" />
          </div>
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_microsoftTeams()" :sub-title="m.subtitle_teamsCredentials()">
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
        <km-toggle v-model="enable_ms_teams" size="sm" :disable="false" />
      </div>
      <template v-if="enable_ms_teams">
        <km-separator class="mb-lg" />
        <km-notification-text :notification="m.hint_teamsCredentialsAgent()" />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Client ID</div>
        <km-input v-model="ms_teams_client_id" :placeholder="m.agents_enterMsTeamsClientId()" />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Tenant ID</div>
        <km-input v-model="ms_teams_tenant_id" :placeholder="m.agents_enterMsTeamsTenantId()" />
        <km-encrypted-input class="mt-md" :value="ms_teams_secret_value" :encrypted-value="has_ms_teams_secret_value" :label="m.agents_secretValue()" :placeholder="m.agents_enterMsTeamsSecretValue()" fake-encrypted-value="******" @update:value="ms_teams_secret_value = $event" />
        <km-notification-text class="mt-lg">
          <div>Check&nbsp;<a class="text-primary cursor-pointer" @click="openHelp">Admin Manual</a>&nbsp;for further steps on MS Teams Agent installation</div>
        </km-notification-text>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_slack()" :sub-title="m.subtitle_slackCredentials()">
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
        <km-toggle v-model="enable_slack" size="sm" :disable="false" />
      </div>
      <template v-if="enable_slack">
        <km-separator class="mb-lg" />
        <km-notification-text :notification="m.hint_slackCredentialsAgent()" />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Client ID</div>
        <km-input v-model="slack_client_id" :placeholder="m.agents_enterSlackClientId()" />
        <km-encrypted-input class="mt-md" :value="slack_token" :encrypted-value="has_slack_encryptes.token" :label="m.agents_token()" :placeholder="m.agents_enterSlackToken()" fake-encrypted-value="******" @update:value="slack_token = $event" />
        <km-encrypted-input class="mt-md" :value="slack_client_secret" :encrypted-value="has_slack_encryptes.client_secret" :label="m.agents_clientSecret()" :placeholder="m.agents_enterSlackClientSecret()" fake-encrypted-value="******" @update:value="slack_client_secret = $event" />
        <km-encrypted-input class="mt-md" :value="slack_signing_secret" :encrypted-value="has_slack_encryptes.signing_secret" :label="m.agents_signingSecret()" :placeholder="m.agents_enterSlackSigningSecret()" fake-encrypted-value="******" @update:value="slack_signing_secret = $event" />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Agent Scopes</div>
        <km-input v-model="slack_scopes" :placeholder="m.agents_enterSlackScopes()" />
        <km-btn class="mt-md" :label="m.agents_connectToSlack()" tone="inverse" :disable="isSlackInstallDisabled" :content-style="&quot;width: auto;&quot;" @click="openSlackInstall" />
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_whatsApp()" :sub-title="m.subtitle_whatsApp()">
      <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">
        <km-toggle v-model="enable_whatsapp" size="sm" :disable="false" />
      </div>
      <template v-if="enable_whatsapp">
        <km-separator class="mb-lg" />
        <km-notification-text :notification="m.hint_whatsAppCredentialsAgent()" />
        <div class="km-field text-secondary-text pb-xs pl-sm mt-lg">Phone Number ID</div>
        <km-input v-model="whatsapp_phone_number_id" :placeholder="m.agents_enterWhatsappPhoneNumberId()" />
        <km-encrypted-input class="mt-md" :value="whatsapp_token" :encrypted-value="has_whatsapp_encrypted.token" :label="m.agents_token()" :placeholder="m.agents_enterWhatsappToken()" fake-encrypted-value="******" @update:value="whatsapp_token = $event" />
        <km-encrypted-input class="mt-md" :value="whatsapp_app_secret" :encrypted-value="has_whatsapp_encrypted.app_secret" :label="m.agents_appSecret()" :placeholder="m.agents_enterWhatsappAppSecret()" fake-encrypted-value="******" @update:value="whatsapp_app_secret = $event" />
        <km-notification-text class="mt-lg">
          <div>Check&nbsp;<a class="text-primary cursor-pointer" @click="openHelp">Admin Manual</a>&nbsp;for further steps on WhatsApp Agent installation</div>
        </km-notification-text>
      </template>
    </km-section>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useAppStore } from '@/stores/appStore'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { copyToClipboard } from '@ds/utils/clipboard'

const { draft, updateHighLevelNestedProperty } = useAgentEntityDetail()
const appStore = useAppStore()

const themeOptions = ref([
  { label: 'Oracle Redwood', value: 'siebel' },
  { label: 'Salesforce', value: 'salesforce' },
  { label: 'Magnet Dark', value: 'dark' },
])
const system_name = computed(() => {
  return draft.value?.system_name || ''
})
const appUrl = computed(() => {
  let panelUrl = `${appStore.config?.panel?.baseUrl}/#/?agent=${system_name.value}`

  if (panelUrl.startsWith('/')) {
    panelUrl = `${window.location.origin}${panelUrl}`
  }

  return panelUrl
})

const enable_iframe = computed({
  get() {
    return draft.value?.channels?.web?.enabled || false
  },
  set(value) {
    updateHighLevelNestedProperty('channels.web.enabled', value)
  },
})

const theme = computed({
  get() {
    const theme = draft.value?.channels?.web?.theme || 'siebel'
    return themeOptions.value.find((option) => option.value === theme)
  },
  set(value) {
    updateHighLevelNestedProperty('channels.web.theme', value.value)
  },
})
const show_close_button = computed({
  get() {
    const web = draft.value?.channels?.web
    return web.hasOwnProperty('show_close_button') ? web.show_close_button : false
  },
  set(value) {
    updateHighLevelNestedProperty('channels.web.show_close_button', value)
  },
})
const isIconHide = computed({
  get() {
    return !draft.value?.channels?.web?.is_icon_hide
  },
  set(value) {
    updateHighLevelNestedProperty('channels.web.is_icon_hide', !value)
  },
})

const openInNewTab = () => {
  window.open(appUrl.value, '_blank')
}

const copy = () => {
  copyToClipboard(appUrl.value)
}

// Teams
const enable_ms_teams = computed({
  get() {
    return draft.value?.channels?.ms_teams?.enabled || false
  },
  set(value) {
    updateHighLevelNestedProperty('channels.ms_teams.enabled', value)
  },
})
const ms_teams_client_id = computed({
  get() {
    return draft.value?.channels?.ms_teams?.client_id || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.ms_teams.client_id', value)
  },
})
const ms_teams_tenant_id = computed({
  get() {
    return draft.value?.channels?.ms_teams?.tenant_id || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.ms_teams.tenant_id', value)
  },
})
const ms_teams_secret_value = computed({
  get() {
    return draft.value?.channels?.ms_teams?.secret_value || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.ms_teams.secret_value', value)
  },
})

const has_ms_teams_secret_value = computed(() => {
  return draft.value?.channels?.ms_teams?.secret_value_encrypted || false
})

// Slack
const enable_slack = computed({
  get() {
    return draft.value?.channels?.slack?.enabled || false
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.enabled', value)
  },
})
const slack_client_id = computed({
  get() {
    return draft.value?.channels?.slack?.client_id || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.client_id', value)
  },
})
const slack_token = computed({
  get() {
    return draft.value?.channels?.slack?.token || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.token', value)
  },
})

const slack_client_secret = computed({
  get() {
    return draft.value?.channels?.slack?.client_secret || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.client_secret', value)
  },
})
const slack_signing_secret = computed({
  get() {
    return draft.value?.channels?.slack?.signing_secret || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.signing_secret', value)
  },
})

const slack_scopes = computed({
  get() {
    return draft.value?.channels?.slack?.agent_scopes || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.slack.agent_scopes', value)
  },
})
const has_slack_encryptes = computed(() => {
  return {
    token: draft.value?.channels?.slack?.token_encrypted || false,
    signing_secret: draft.value?.channels?.slack?.signing_secret_encrypted || false,
    client_secret: draft.value?.channels?.slack?.client_secret_encrypted || false,
  }
})

const enable_whatsapp = computed({
  get() {
    return draft.value?.channels?.whatsapp?.enabled || false
  },
  set(value) {
    updateHighLevelNestedProperty('channels.whatsapp.enabled', value)
  },
})
const whatsapp_phone_number_id = computed({
  get() {
    return draft.value?.channels?.whatsapp?.phone_number_id || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.whatsapp.phone_number_id', value)
  },
})
const whatsapp_token = computed({
  get() {
    return draft.value?.channels?.whatsapp?.token || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.whatsapp.token', value)
  },
})
const whatsapp_app_secret = computed({
  get() {
    return draft.value?.channels?.whatsapp?.app_secret || ''
  },
  set(value) {
    updateHighLevelNestedProperty('channels.whatsapp.app_secret', value)
  },
})
const has_whatsapp_encrypted = computed(() => {
  return {
    token: draft.value?.channels?.whatsapp?.token_encrypted || false,
    app_secret: draft.value?.channels?.whatsapp?.app_secret_encrypted || false,
  }
})

const slackInstallUrl = computed(() => {
  const baseUrl = appStore.config?.api?.aiBridge?.urlUser
  if (!baseUrl) return null
  return `${baseUrl}/agents/slack/install?agent=${encodeURIComponent(system_name.value)}`
})

const isSlackInstallDisabled = computed(() => {
  const hasClientId = !!slack_client_id.value?.trim()
  return !hasClientId || !slackInstallUrl.value
})
const openSlackInstall = () => {
  window.open(`${appStore.config?.api?.aiBridge?.urlUser}/agents/slack/install?agent=${system_name.value}`, '_blank')
}

const openHelp = () => {
  window.open('/help/docs/en/', '_blank')
}
</script>
