<template lang="pug">
.column.search-prompt-container.border-radius-12.q-mb-16.full-width.q-gap-8
  .row
    km-input.full-width(
      ref='input',
      autogrow,
      placeholder='Type your question here',
      :model-value='prompt',
      @input='prompt = $event',
      @keydown.enter='submit',
      border-radius='8px',
      height='var(--prompt-input-height)'
    )
      template(#append='{ height }')
        .self-end.center-flex(:style='{ height }')
          q-btn.border-radius-6(color='primary', @click='getAnswer', unelevated, :padding='$theme != "salesforce" ? "6px 7px" : "9px 17px 9px 17px"')
            template(v-slot:default)
              q-icon(name='fas fa-search', size='var(--prompt-input-icon-size)')
</template>

<script>
import { useSearch } from '@/pinia'
import { storeToRefs } from 'pinia'

export default {
  expose: ['refine'],
  props: {
    hideCollectionPicker: {
      default: false,
      type: Boolean,
    },
    rag: {
      default: false,
      type: Boolean,
    },
    // eslint-disable-next-line vue/prop-name-casing
    rag_code: {
      type: String,
      default: '',
    },
  },
  emits: ['onLoad'],
  setup() {
    const searchStore = useSearch()
    const { searchPrompt: prompt, answersLoading: loading } = storeToRefs(searchStore)

    return {
      prompt,
      loading,
      searchStore,
    }
  },
  computed: {},
  watch: {},
  created() {},
  mounted() {},
  methods: {
    refine(question) {
      this.prompt = question
      this.$refs?.input.focus()
    },
    submit(event) {
      if (!event.shiftKey) {
        event.preventDefault()
        this.getAnswer()
      }
    },
    async getAnswer() {
      this.searchStore.getAnswerRagExecute(this.rag_code)

      this.prompt = ''
      this.$refs?.input.blur()
      this.$emit('onLoad')
    },
  },
}
</script>

<style lang="stylus">
.search-btn
  min-height: 30px;
  padding: 5px 8px;
  // opacity: 0.5;

  .q-icon
    font-size: 16px;
</style>

<style lang="stylus" scoped>
.search-prompt-container
  min-width: 450px;
  max-width: 800px;
  width: 100%;
@media (max-width: 500px)
  .search-prompt-container
    min-width: unset
    max-width: unset
</style>
