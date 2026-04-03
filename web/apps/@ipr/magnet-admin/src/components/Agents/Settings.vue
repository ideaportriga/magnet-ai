<template lang="pug">
div
  km-section(:title='m.section_welcomeMessage()', :subTitle='m.subtitle_configureGreeting()')
    .km-field.text-secondary-text.q-pb-sm.q-pl-8 {{ m.section_welcomeMessage() }}
      km-input(ref='input', rows='8', border-radius='8px', height='36px', type='textarea', v-model='settingsWelcomeMessage')
  q-separator.q-my-lg
  km-section(:title='m.section_userFeedback()', :subTitle='m.subtitle_allowFeedback()')
    q-toggle(v-model='settingsUserFeedback', color='primary')
  q-separator.q-my-lg
  km-section(:title='m.section_sampleQuestions()', :subTitle='m.subtitle_sampleQuestions()')
    q-toggle(v-model='settingsSampleQuestions', color='primary')
    template(v-if='settingsSampleQuestions')
      .q-mb-lg
        .km-input-label {{ m.common_question1() }}
        km-input(v-model='question1', placeholder='What are our most popular pricing plans?')
      .q-mb-lg
        .km-input-label {{ m.common_question2() }}
        km-input(v-model='question2', placeholder='How to change password in mobile application?')
      div
        .km-input-label {{ m.common_question3() }}
        km-input(v-model='question3', placeholder='What is the maximum discount that can be applied on top of other discounts?')
  q-separator.q-my-lg
  km-section(:title='m.section_memoryStrategy()', :subTitle='m.subtitle_controlMemory()')
    q-btn-toggle(
      v-model='memoryStrategy',
      toggle-color='primary-light',
      :options='memoryStrategyOptions',
      dense,
      text-color='text-weak',
      toggle-text-color='primary'
    )
    template(v-if='memoryStrategy === "last_n"')
      .q-mt-md
        .km-input-label {{ m.agents_lastNMessages() }}
        km-input(v-model='memoryLastNMessages', type='number', placeholder='10', height='36px')
  q-separator.q-my-lg
</template>

<script>
import { m } from '@/paraglide/messages'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

const intervals = [
  { label: '1 day', value: '1D' },
  { label: '3 day', value: '3D' },
  { label: '1 week', value: '7D' },
]

const memoryStrategyOptions = [
  { label: 'Last N messages', value: 'last_n' },
  { label: 'All messages', value: 'all' },
]

export default {
  setup() {
    const { draft, activeVariant, updateVariantField } = useAgentEntityDetail()
    return {
      m,
      draft,
      activeVariant,
      updateVariantField,
      intervals,
      memoryStrategyOptions,
    }
  },

  computed: {
    settingsWelcomeMessage: {
      get() {
        return this.activeVariant?.value?.settings?.welcome_message || ''
      },
      set(value) {
        this.updateVariantField('settings.welcome_message', value)
      },
    },
    settingsUserFeedback: {
      get() {
        return this.activeVariant?.value?.settings?.user_feedback || false
      },
      set(value) {
        this.updateVariantField('settings.user_feedback', value)
      },
    },
    settingsSampleQuestions: {
      get() {
        return this.activeVariant?.value?.settings?.sample_questions?.enabled || false
      },
      set(value) {
        this.updateVariantField('settings.sample_questions.enabled', value)
      },
    },
    question1: {
      get() {
        return this.activeVariant?.value?.settings?.sample_questions?.questions?.question1 || ''
      },
      set(value) {
        this.updateVariantField('settings.sample_questions.questions.question1', value)
      },
    },
    question2: {
      get() {
        return this.activeVariant?.value?.settings?.sample_questions?.questions?.question2 || ''
      },
      set(value) {
        this.updateVariantField('settings.sample_questions.questions.question2', value)
      },
    },
    question3: {
      get() {
        return this.activeVariant?.value?.settings?.sample_questions?.questions?.question3 || ''
      },
      set(value) {
        this.updateVariantField('settings.sample_questions.questions.question3', value)
      },
    },
    memoryStrategy: {
      get() {
        return this.activeVariant?.value?.settings?.memory_strategy || 'last_n'
      },
      set(value) {
        this.updateVariantField('settings.memory_strategy', value)
      },
    },
    memoryLastNMessages: {
      get() {
        return this.activeVariant?.value?.settings?.memory_last_n_messages ?? null
      },
      set(value) {
        const parsed = value === '' || value === null ? null : Number(value)
        this.updateVariantField('settings.memory_last_n_messages', parsed)
      },
    },
  },
}
</script>
