<template lang="pug">
div.q-mr-8
  km-section(title='Web', subTitle='Make the Agent available as an iframe')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16
      q-toggle(v-model='enable_iframe', color='primary', size='sm', :disable='false')
    template(v-if='enable_iframe')
      q-separator
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Theme
      .row.items-center.q-gap-16.no-wrap(style="width: 220px")
        km-select(v-model='theme', :options='themeOptions', color='primary', size='sm', :disable='false' style="width: 220px")
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Show Close button
        q-toggle(v-model='show_close_button', color='primary', size='sm', :disable='false')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Show Logo
        q-toggle(v-model='isIconHide', color='primary', size='sm', :disable='false')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 URL
      .row
        .col.q-mr-sm
          km-input(ref='input', border-radius='8px', height='36px', :readonly='true', :model-value='appUrl')
        .col-auto
          km-btn(icon='fas fa-copy', iconSize='16px', size='sm', flat, @click='copy', tooltip='Copy')
        .col-auto
          km-btn(icon='fas fa-external-link-alt', iconSize='16px', size='sm', flat, @click='openInNewTab', tooltip='Open in new tab')
  q-separator.q-my-lg
  km-section(title='Ms Teams', subTitle='Make the Agent available as a mobile app')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16
      q-toggle(v-model='enable_ms_teams', color='primary', size='sm', :disable='false')
    template(v-if='enable_ms_teams')
      q-separator.q-mb-lg
      km-notification-text(
        notification='MS Teams credentials are stored on Agent level, not on the variant.' 
      )
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Client ID
      km-input(v-model='ms_teams_client_id', placeholder='Enter MS Teams Client ID')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Tenant ID
      km-input(v-model='ms_teams_tenant_id', placeholder='Enter MS Teams Tenant ID')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Secret value
      km-input(
        v-model='ms_teams_secret_value',
        :type='"password"',
        :placeholder='has_ms_teams_secret_value ? "Saved (leave blank to keep)" : "Enter MS Teams Secret Value"'
      )
      km-notification-text.q-mt-lg
        div Check&nbsp;
          a.text-primary(href='https://docs.magnet.ai/docs/admin-manual/ms-teams-agent', target='_blank') Admin Manual
          | &nbsp;for further steps on MS Teams Agent installation
  q-separator.q-my-lg
  km-section(title='Slack', subTitle='Make the Agent available as a Slack app')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16
      q-toggle(v-model='enable_slack', color='primary', size='sm', :disable='false')
    template(v-if='enable_slack')
      q-separator.q-mb-lg
      km-notification-text(
        notification='Slack credentials are stored on Agent level, not on the variant.' 
      )
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Client ID
      km-input(v-model='slack_client_id', placeholder='Enter Slack Client ID')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Token
      km-input(v-model='slack_token', placeholder='Enter Slack Token', :type='"password"', :placeholder='has_slack_encryptes.token ? "Saved (leave blank to keep)" : "Enter Slack Token"')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Client Secret
      km-input(v-model='slack_client_secret', placeholder='Enter Slack Client Secret', :type='"password"', :placeholder='has_slack_encryptes.client_secret ? "Saved (leave blank to keep)" : "Enter Slack Client Secret"')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Signing Secret
      km-input(v-model='slack_signing_secret', placeholder='Enter Slack Signing Secret', :type='"password"', :placeholder='has_slack_encryptes.signing_secret ? "Saved (leave blank to keep)" : "Enter Slack Signing Secret"')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 State Secret
      km-input(v-model='slack_state_secret', placeholder='Enter Slack State Secret', :type='"password"', :placeholder='has_slack_encryptes.state_secret ? "Saved (leave blank to keep)" : "Enter Slack State Secret"')
      .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-16 Agent Scopes
      km-input(v-model='slack_scopes', placeholder='Enter Slack Agent Scopes (comma separated)')
      km-btn(label='Connect to Slack', color='white', @click='openSlackInstall', :disable='isSlackInstallDisabled', :contentStyle='"width: auto;"').q-mt-md

</template>
<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { copyToClipboard } from 'quasar'


const store = useStore()


const themeOptions = ref([
  { label: 'Oracle Redwood', value: 'siebel' },
  { label: 'Salesforce', value: 'salesforce' },
])
const system_name = computed(() => {
  return store.getters.agent_detail?.system_name || ''
})
const appUrl = computed(() => {
  let panelUrl = `${store.getters.config?.panel?.baseUrl}/#/?agent=${system_name.value}`

  if (panelUrl.startsWith('/')) {
    panelUrl = `${window.location.origin}${panelUrl}`
  }

  return panelUrl
})

const enable_iframe = computed({
  get(){
    return store.getters.agent_detail?.channels?.web?.enabled || false
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.web.enabled', value: value })
  }
})

const theme = computed({
  get(){
    const theme = store.getters.agent_detail?.channels?.web?.theme || 'siebel'
    return themeOptions.value.find((option) => option.value === theme)
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.web.theme', value: value.value })
  }
})
const show_close_button = computed({
  get(){
    const web = store.getters.agent_detail?.channels?.web
    return web.hasOwnProperty('show_close_button') ? web.show_close_button : true
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.web.show_close_button', value: value })
  }
})
const isIconHide = computed({
  get(){
    return !store.getters.agent_detail?.channels?.web?.is_icon_hide
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.web.is_icon_hide', value: !value })
  }
})

const openInNewTab = () => {
  window.open(appUrl.value, '_blank')
}

const copy = () => {
  copyToClipboard(appUrl.value)
}

// Teams
const enable_ms_teams = computed({
  get(){
    return store.getters.agent_detail?.channels?.ms_teams?.enabled || false
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.ms_teams.enabled', value: value })
  }
})
const ms_teams_client_id = computed({
  get(){
    return store.getters.agent_detail?.channels?.ms_teams?.client_id || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.ms_teams.client_id', value: value })
  }
})
const ms_teams_tenant_id = computed({
  get(){
    return store.getters.agent_detail?.channels?.ms_teams?.tenant_id || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.ms_teams.tenant_id', value: value })
  }
})
const ms_teams_secret_value = computed({
  get(){
    return store.getters.agent_detail?.channels?.ms_teams?.secret_value || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.ms_teams.secret_value', value: value })
  }
})

const has_ms_teams_secret_value = computed(() => {
  // TODO: map to actual secrets when we have them 
  return false
})

// Slack
const enable_slack = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.enabled || false
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.enabled', value: value })
  }
})
const slack_client_id = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.client_id || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.client_id', value: value })
  }
})
const slack_token = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.token || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.token', value: value })
  }
})

const slack_client_secret = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.client_secret || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.client_secret', value: value })
  }
})
const slack_signing_secret = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.signing_secret || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.signing_secret', value: value })
  }
})
const slack_scopes = computed({
  get(){
    return store.getters.agent_detail?.channels?.slack?.scopes || ''
  },
  set(value){
    store.dispatch('updateNestedHighLevelAgentDetailProperty', { path: 'channels.slack.scopes', value: value })
  }
})
const has_slack_encryptes = computed(() => {
  // TODO: map to actual secrets when we have them 
  return {
    token: false,  
    signing_secret: false,
    client_secret: false,
    state_secret: false,
  }
})

const isSlackInstallDisabled = computed(() => {
  const hasClientId = !!slack_client_id.value?.trim()
  return !hasClientId || !slackInstallUrl.value
})
const openSlackInstall = () => {
  window.open(`${store.getters.config?.api?.aiBridge?.urlUser}/agents/slack/install?agent=${system_name.value}`, '_blank')
}



</script>