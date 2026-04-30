<template>
  <div
    class="cluster full-height p-lg fit relative-position bl-border"
    data-wrap="no"
    data-justify="center"
  >
    <div class="stack search-container">
      <div class="flex-1">
        <div class="stack full-height pb-md relative-position">
          <template v-if="uiSettings?.header_configuration?.header">
            <div
              class="cluster pb-md pt-md full-width text-center"
              data-justify="center"
              data-gap="xs"
            >
              <div class="km-heading-5">
                {{ uiSettings?.header_configuration?.header }}
              </div>
            </div>
            <div
              v-if="uiSettings?.header_configuration?.sub_header"
              class="cluster pb-md full-width"
              data-justify="center"
              data-gap="xs"
            >
              <div class="km-heading-2 text-center pb-lg">
                {{ uiSettings?.header_configuration?.sub_header }}
              </div>
            </div>
          </template>
          <div class="bg-user-input-bg px-lg">
            <retrieval-prompt
              ref="prompt"
              class="mt-md"
              hide-collection-picker
              :retrieval_tool="retrieval_tool"
              @on-load="scrollTop"
            />
          </div>
          <template v-if="isShowHints">
            <div class="cluster mt-lg mb-sm">
              <div class="flex-1 km-heading-3">
                {{ m.common_youCanAskLikeThis() }}
              </div>
              <div class="flex-none">
                <km-btn
                  flat
                  tone="brand"
                  @click="showHints = false"
                >
                  <div class="km-button-text">
                    {{ m.common_dontShowHints() }}
                  </div>
                </km-btn>
              </div>
            </div>
            <!-- Hints-->
            <template v-if="$theme === &quot;default&quot;">
              <template
                v-for="(item, index) in sampleQuestion"
                :key="index"
              >
                <km-btn
                  flat
                  @click="refine(item)"
                >
                  <div class="wrapped-text">
                    {{ item }}
                  </div>
                </km-btn>
              </template>
            </template>
            <template v-else>
              <template
                v-for="(item, index) in sampleQuestion"
                :key="index"
              >
                <div class="flex">
                  <km-btn
                    class="hint"
                    flat
                    tone="brand"
                    @click="refine(item)"
                  >
                    <div class="wrapped-text">
                      {{ item }}
                    </div>
                  </km-btn>
                </div>
              </template>
            </template>
          </template>
          <template v-if="answers.length || loading">
            <km-scroll-area
              ref="scroll"
              class="full-height flex-1"
            >
              <div
                class="stack mt-md"
                data-gap="lg"
              >
                <template v-if="loading">
                  <div
                    class="cluster border-radius-12 bg-white p-lg"
                    data-justify="center"
                    data-gap="lg"
                  >
                    <km-loader
                      size="62px"
                    />
                  </div>
                </template>
                <template
                  v-for="(answer, index) in answers"
                  :key="index"
                >
                  <retrieval-answer-tab
                    :answer="answer"
                    :ui-settings="uiSettings"
                    @refine="refine"
                  />
                </template>
              </div>
            </km-scroll-area>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { useSearch, useAiApps } from '@/pinia'
import { storeToRefs } from 'pinia'

export default {
  props: {
    index: Number,
    open: Boolean,
    // eslint-disable-next-line vue/prop-name-casing
    retrieval_tool: {
      type: String,
      default: '',
    },
  },
  setup() {
    const searchStore = useSearch()
    const { answers, answersLoading: loading } = storeToRefs(searchStore)

    const aiAppsStore = useAiApps()
    const { app, displayTab } = storeToRefs(aiAppsStore)

    return {
      loading,
      answers,
      showHints: ref(true),
      app,
      displayTab,
      searchStore,
      m,
    }
  },
  computed: {
    panel() {
      return this.displayTab
    },
    tool() {
      return this.panel?.entityObject
    },

    uiSettings() {
      return this.tool?.ui_settings
    },
    systemName() {
      return this.tool?.system_name || ''
    },
    isShowHints() {
      return (
        this.answers?.length == 0 &&
        this.showHints &&
        this.uiSettings?.sample_questions?.enabled &&
        (!!this.uiSettings?.sample_questions?.questions?.question1 ||
          !!this.uiSettings?.sample_questions?.questions?.question2 ||
          !!this.uiSettings?.sample_questions?.questions?.question3)
      )
    },
    sampleQuestion() {
      return this.uiSettings.sample_questions?.questions
    },
  },
  watch: {
    systemName(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.clearAnswers()
      }
    },
  },
  created() {},
  mounted() {
    this.clearAnswers()
  },
  methods: {
    clearAnswers() {
      this.searchStore.clearAnswers()
    },
    refine(question) {
      this.$refs?.prompt?.refine(question)
    },
    scrollTop() {
      this.$refs?.scroll?.setScrollPosition?.('vertical', 0, 200)
    },
  },
}
</script>

<style scoped>
.search-container {
  min-inline-size: 450px;
  max-inline-size: 800px;
  inline-size: 100%;
}
@media (max-width: 500px) {
  .search-container {
    min-inline-size: unset;
    max-inline-size: unset;
  }
}
</style>
