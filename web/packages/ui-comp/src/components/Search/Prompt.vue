<template lang="pug">
.column.search-prompt-container.border-radius-12.q-mb-16.full-width.q-gap-8
  .row
    km-input.full-width(
      data-test='search-input',
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
          q-btn.border-radius-6(
            data-test='search-btn',
            color='primary',
            @click='getAnswer',
            unelevated,
            :padding='$theme != "salesforce" ? "6px 7px" : "9px 17px 9px 17px"'
          )
            template(v-slot:default)
              q-icon(name='fas fa-search', size='var(--prompt-input-icon-size)')
</template>

<script>
import useState from '@shared/composables/useState'

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
    searchString: {
      type: String,
      default: '',
    },
  },
  emits: ['onLoad'],
  setup() {
    const prompt = useState('searchPrompt')
    const loading = useState('answersLoading')
    return {
      prompt,
      loading,
    }
  },
  computed: {},
  watch: {
    searchString: {
      deep: true,
      handler(next, prev) {
        if (prev !== next) {
          this.prompt = next || ''
        }
      },
    },
  },
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
      if (this.rag) {
        await this.$store.dispatch('getAnswerRag')
      } else {
        await this.$store.dispatch('getAnswerRagExecute', this.rag_code)
      }

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
