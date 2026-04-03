<template lang="pug">
div
  km-section(:title='m.section_headerConfiguration()', :subTitle='m.subtitle_configureRagHeading()')
    .q-mb-lg
      .km-input-label {{ m.ragTools_headingText() }}
      km-input(@input='headingText = $event', :model-value='headingText', :placeholder='m.ragTools_headingPlaceholder()')
      .km-tiny {{ m.ragTools_notDisplayedIfBlank() }}
    div
      .km-input-label {{ m.ragTools_subheadingText() }}
      km-input(@input='subHeadingText = $event', :model-value='subHeadingText', :placeholder='m.ragTools_subheadingPlaceholder()')
      .km-tiny {{ m.ragTools_notDisplayedIfBlank() }}
  q-separator.q-my-lg
  km-section(:title='m.section_userFeedback()', :subTitle='m.subtitle_allowFeedback()')
    q-toggle.q-mb-lg(v-model='isUserFeedbackOn', dense)
  q-separator.q-my-lg
  km-section(:title='m.section_sampleQuestions()', :subTitle='m.subtitle_sampleQuestions()')
    q-toggle.q-mb-lg(v-model='isSampleQestion', dense)
    template(v-if='isSampleQestion')
      .q-mb-lg
        .km-input-label {{ m.common_question1() }}
        km-input(v-model='question1', :placeholder='m.ragTools_sampleQuestion1Placeholder()')
      .q-mb-lg
        .km-input-label {{ m.common_question2() }}
        km-input(v-model='question2', :placeholder='m.ragTools_sampleQuestion2Placeholder()')
      div
        .km-input-label {{ m.common_question3() }}
        km-input(v-model='question3', :placeholder='m.ragTools_sampleQuestion3Placeholder()')
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
