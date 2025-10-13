<template lang="pug">
div
  km-section(title='Welcome message', subTitle='Configure default agent message, e.g. greeting')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 Welcome message
      km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='settingsWelcomeMessage')
  q-separator.q-my-lg
  km-section(
    title='User feedback',
    subTitle='Allow users to send their feedback in form of like or dislike.'
  )
    q-toggle(
      v-model='settingsUserFeedback',
      color='primary',
    )
  q-separator.q-my-lg
  km-section(
    title='Sample questions',
    subTitle='Display up to 3 question suggestions to help users formulate their questions.'
  )
    q-toggle(
      v-model='settingsSampleQuestions',
      color='primary',
    )
    template(v-if='settingsSampleQuestions')
      .q-mb-lg
        .km-input-label Question 1
        km-input(v-model='question1', placeholder='What are our most popular pricing plans?')
      .q-mb-lg
        .km-input-label Question 2
        km-input(v-model='question2', placeholder='How to change password in mobile application?')
      div
        .km-input-label Question 3
        km-input(v-model='question3', placeholder='What is the maximum discount that can be applied on top of other discounts?')
  q-separator.q-my-lg

  km-section(
    title='Agent credentials',
    subTitle='Provide identifiers and a secret to be used by the agent.'
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
</template>

<script>

const intervals = [
  { label: '1 day', value: '1D' },
  { label: '3 day', value: '3D' },
  { label: '1 week', value: '7D' },
]

export default {

  setup() {
    return {
      intervals,
    }
  },
  data() {
    return {
      secret_value_local: '',
    }
  },

  computed: {
    settingsWelcomeMessage: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.welcome_message || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.welcome_message', value })
      },
    },
    settingsUserFeedback: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.user_feedback || false
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.user_feedback', value })
      },
    },
    settingsSampleQuestions: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.enabled || false
      },
      set(value) {

        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.sample_questions.enabled', value })
      },
    },
    question1: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question1 || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.sample_questions.questions.question1', value })
      },
    },
    question2: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question2 || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.sample_questions.questions.question2', value })
      },
    },
    question3: {
      get() {
        return this.$store.getters.agentDetailVariant?.value?.settings?.sample_questions?.questions?.question3 || ''
      },
      set(value) {
        this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'settings.sample_questions.questions.question3', value })
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
  },
  watch: {
    secret_value_local(newVal) {
      if (!newVal) return
      this.$store.dispatch('updateNestedAgentDetailProperty', { path: 'secrets_encrypted.secret_value', value: newVal })
    },
  },
}
</script>
