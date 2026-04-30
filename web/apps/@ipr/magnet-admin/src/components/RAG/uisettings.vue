<template>
  <div>
    <km-section :title="m.section_headerConfiguration()" :sub-title="m.subtitle_configureRagHeading()">
      <div class="mb-lg">
        <div class="km-input-label">{{ m.ragTools_headingText() }}</div>
        <km-input :model-value="headingText" :placeholder="m.ragTools_headingPlaceholder()" @input="headingText = $event" />
        <div class="km-tiny">{{ m.ragTools_notDisplayedIfBlank() }}</div>
      </div>
      <div>
        <div class="km-input-label">{{ m.ragTools_subheadingText() }}</div>
        <km-input :model-value="subHeadingText" :placeholder="m.ragTools_subheadingPlaceholder()" @input="subHeadingText = $event" />
        <div class="km-tiny">{{ m.ragTools_notDisplayedIfBlank() }}</div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_userFeedback()" :sub-title="m.subtitle_allowFeedback()">
      <km-toggle v-model="isUserFeedbackOn" class="mb-lg" dense />
    </km-section>
    <km-separator class="my-lg" />
    <km-section :title="m.section_sampleQuestions()" :sub-title="m.subtitle_sampleQuestions()">
      <km-toggle v-model="isSampleQestion" class="mb-lg" dense />
      <template v-if="isSampleQestion">
        <div class="mb-lg">
          <div class="km-input-label">{{ m.common_question1() }}</div>
          <km-input v-model="question1" :placeholder="m.ragTools_sampleQuestion1Placeholder()" />
        </div>
        <div class="mb-lg">
          <div class="km-input-label">{{ m.common_question2() }}</div>
          <km-input v-model="question2" :placeholder="m.ragTools_sampleQuestion2Placeholder()" />
        </div>
        <div>
          <div class="km-input-label">{{ m.common_question3() }}</div>
          <km-input v-model="question3" :placeholder="m.ragTools_sampleQuestion3Placeholder()" />
        </div>
      </template>
    </km-section>
  </div>
</template>

<script>
import { m } from '@/paraglide/messages'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'

export default {
  props: [],
  emits: [],

  setup() {
    const { activeVariant, updateVariantField } = useVariantEntityDetail('rag_tools')
    return { m, activeVariant, updateVariantField }
  },
  computed: {
    isAllowToBypassCache: {
      get() {
        return this.activeVariant?.ui_settings?.offer_to_bypass_cache || false
      },
      set(value) {
        this.updateVariantField('ui_settings.offer_to_bypass_cache', value)
      },
    },
    isUserFeedbackOn: {
      get() {
        return this.activeVariant?.ui_settings?.user_fideback || false
      },
      set(value) {
        this.updateVariantField('ui_settings.user_fideback', value)
      },
    },
    headingText: {
      get() {
        return this.activeVariant?.ui_settings?.header_configuration?.header || ''
      },
      set(value) {
        this.updateVariantField('ui_settings.header_configuration.header', value)
      },
    },
    subHeadingText: {
      get() {
        return this.activeVariant?.ui_settings?.header_configuration?.sub_header || ''
      },
      set(value) {
        this.updateVariantField('ui_settings.header_configuration.sub_header', value)
      },
    },
    isShowLinkTitlesOn: {
      get() {
        return true
      },
    },
    isSampleQestion: {
      get() {
        return this.activeVariant?.ui_settings?.sample_questions?.enabled || false
      },
      set(value) {
        this.updateVariantField('ui_settings.sample_questions.enabled', value)
      },
    },
    question1: {
      get() {
        return this.activeVariant?.ui_settings?.sample_questions?.questions?.question1
      },
      set(value) {
        this.updateVariantField('ui_settings.sample_questions.questions.question1', value)
      },
    },
    question2: {
      get() {
        return this.activeVariant?.ui_settings?.sample_questions?.questions?.question2
      },
      set(value) {
        this.updateVariantField('ui_settings.sample_questions.questions.question2', value)
      },
    },
    question3: {
      get() {
        return this.activeVariant?.ui_settings?.sample_questions?.questions?.question3
      },
      set(value) {
        this.updateVariantField('ui_settings.sample_questions.questions.question3', value)
      },
    },
  },
  created() {},
  methods: {},
}
</script>
