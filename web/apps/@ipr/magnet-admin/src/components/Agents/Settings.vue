<template>
  <div>
    <km-section :title="m.section_welcomeMessage()" :sub-title="m.subtitle_configureGreeting()">
      <div class="km-field text-secondary-text pb-sm pl-sm">
        {{ m.section_welcomeMessage() }}
        <km-input ref="input" v-model="settingsWelcomeMessage" rows="8" border-radius="8px" height="36px" type="textarea" />
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_userFeedback()" :sub-title="m.subtitle_allowFeedback()">
      <km-toggle v-model="settingsUserFeedback" />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_sampleQuestions()" :sub-title="m.subtitle_sampleQuestions()">
      <km-toggle v-model="settingsSampleQuestions" />
      <template v-if="settingsSampleQuestions">
        <div class="mb-lg">
          <div class="km-input-label">{{ m.common_question1() }}</div>
          <km-input v-model="question1" :placeholder="m.agents_sampleQuestion1Default()" />
        </div>
        <div class="mb-lg">
          <div class="km-input-label">{{ m.common_question2() }}</div>
          <km-input v-model="question2" :placeholder="m.agents_sampleQuestion2Default()" />
        </div>
        <div>
          <div class="km-input-label">{{ m.common_question3() }}</div>
          <km-input v-model="question3" :placeholder="m.agents_sampleQuestion3Default()" />
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_memoryStrategy()" :sub-title="m.subtitle_controlMemory()">
      <km-btn-toggle v-model="memoryStrategy" :options="memoryStrategyOptions" dense />
      <template v-if="memoryStrategy === &quot;last_n&quot;">
        <div class="mt-md">
          <div class="km-input-label">{{ m.agents_lastNMessages() }}</div>
          <km-input v-model="memoryLastNMessages" type="number" placeholder="10" height="36px" />
        </div>
      </template>
    </km-section>
    <km-separator class="my-lg" />
  </div>
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
  { label: m.agents_lastNMessages(), value: 'last_n' },
  { label: m.agents_allMessages(), value: 'all' },
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
