<template lang="pug">
div
  km-section(
    title='MS Teams Agent credentials',
    subTitle='Provide identifiers and a secret to be used by the MS Teams agent.'
  )
    .q-mb-lg
      .km-input-label Client ID
      km-input(v-model='client_id', placeholder='Enter client_id')
    .q-mb-lg
      .km-input-label Tenant ID
      km-input(v-model='tenant_id', placeholder='Enter tenant_id')
    .q-mb-lg
      .km-input-label Secret value
      km-input(
        v-model='secret_value_local',
        :type='"password"',
        :placeholder='has_secret_value ? "Saved (leave blank to keep)" : "Enter secret_value"'
      )
  q-separator.q-my-lg
  
  km-section(
    title='Slack Agent Credentials',
    subTitle='Provide identifiers and secrets to be used by the Slack agent.'
  )
    .q-mb-lg
      .km-input-label Client Id
      km-input(v-model='slack_client_id', placeholder='Enter Slack client id')
    .q-mb-lg
      .km-input-label Token
      km-input(
        v-model='slack_token_local',
        :type='"password"',
        :placeholder='has_slack_token ? "Saved (leave blank to keep)" : "Enter Slack token"'
      )
    .q-mb-lg
      .km-input-label Signing Secret
      km-input(
        v-model='slack_signing_secret_local',
        :type='"password"',
        :placeholder='has_slack_signing_secret ? "Saved (leave blank to keep)" : "Enter Slack signing secret"'
      )
    .q-mb-lg
      .km-input-label Client Secret
      km-input(
        v-model='slack_client_secret_local',
        :type='"password"',
        :placeholder='has_slack_client_secret ? "Saved (leave blank to keep)" : "Enter Slack client secret"'
      )
    .q-mb-lg
      .km-input-label State Secret
      km-input(
        v-model='slack_state_secret_local',
        :type='"password"',
        :placeholder='has_slack_state_secret ? "Saved (leave blank to keep)" : "Enter Slack state secret"'
      )
    .q-mb-lg
      .km-input-label Agent Scopes
      km-input(v-model='slack_scopes', placeholder='Enter Slack Scopes (comma separated)')
    .q-mt-md
      .row
        .col-auto
          km-btn(
            label='Connect to Slack',
            color='white',
            @click='openSlackInstall',
            :disable='isSlackInstallDisabled',
            :contentStyle='"width: auto;"'
          )
</template>

<script>
export default {
  data() {
    return {
      secret_value_local: '',
      slack_token_local: '',
      slack_signing_secret_local: '',
      slack_client_secret_local: '',
      slack_state_secret_local: '',
    }
  },
  computed: {
    name: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.credentials?.name || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'credentials.name', value })
      },
    },
    client_id: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.credentials?.client_id || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'credentials.client_id', value })
      },
    },
    tenant_id: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.credentials?.tenant_id || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'credentials.tenant_id', value })
      },
    },
    has_secret_value() {
      return !!this.$store.getters.agentDetailVariant?.value?.secrets_encrypted?.secret_value
    },
    // Slack
    slack_client_id: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.credentials?.slack?.client_id || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'credentials.slack.client_id', value })
      },
    },
    slack_scopes: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.credentials?.slack?.scopes || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'credentials.slack.scopes', value })
      },
    },
    has_slack_token() {
      return !!this.$store.getters.agentDetailVariant?.value?.secrets_encrypted?.slack?.token
    },
    has_slack_signing_secret() {
      return !!this.$store.getters.agentDetailVariant?.value?.secrets_encrypted?.slack?.signing_secret
    },
    has_slack_client_secret() {
      return !!this.$store.getters.agentDetailVariant?.value?.secrets_encrypted?.slack?.client_secret
    },
    has_slack_state_secret() {
      return !!this.$store.getters.agentDetailVariant?.value?.secrets_encrypted?.slack?.state_secret
    },
    agentSystemName() {
      const agent = this.$store.getters.agent_detail
      return agent?.system_name?.trim()
    },
    slackInstallUrl() {
      const baseUrl = this.$store.getters.config?.api?.aiBridge?.urlUser
      if (!baseUrl) return null
      return this.agentSystemName ? `${baseUrl}/agents/slack/install?agent=${encodeURIComponent(this.agentSystemName)}` : null
    },
    isSlackInstallDisabled() {
      const hasClientId = !!this.slack_client_id?.trim()
      return !hasClientId || !this.slackInstallUrl
    },
  },
  watch: {
    secret_value_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.secret_value', value: newVal })
    },
    slack_token_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.slack.token', value: newVal })
    },
    slack_signing_secret_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.slack.signing_secret', value: newVal })
    },
    slack_client_secret_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.slack.client_secret', value: newVal })
    },
    slack_state_secret_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.slack.state_secret', value: newVal })
    },
  },
  methods: {
    openSlackInstall() {
      if (this.isSlackInstallDisabled || !this.slackInstallUrl) return
      window.open(this.slackInstallUrl, '_blank', 'noopener,noreferrer')
    },
  },
}
</script>

