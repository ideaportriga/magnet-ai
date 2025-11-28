<template lang="pug">
.column.bg-white.ba-border.q-px-lg.q-pt-4.q-pb-24.q-gap-16.border-radius-12(:class='{ "no-pointer-events prevent-select opaque": readonly }')
  .km-heading-4.q-pt-24 Test prompt template

  .row.items-center.q-gap-8.q-mt-sm
    .col-auto.q-pl-xs
      .circle-accent
    .col
      //- .km-description.text-secondary-text Test your prompt with text in input below. Prompt will be applied to it automatically.
      .km-description.text-secondary-text Enter text below to test your prompt on top of this text. Your prompt will be applied to it.

  //- QUESTION

  km-input.full-width(
    ref='input',
    autogrow,
    placeholder='Type text to test your prompt',
    :model-value='inputText',
    @input='inputText = $event',
    @keydown.enter='submit',
    border-radius='8px'
  )
    template(v-slot:append)
      .fit.bottom-flex
        q-btn.q-my-6.border-radius-6(color='primary', :disabled='disabled', @click='submit', unelevated, padding='7px 8px')
          template(v-slot:default)
            q-icon(name='fas fa-paper-plane', size='16px')

  //- ANSWER
  template(v-if='loading')
    .row.justify-center
      q-spinner-dots(size='62px', color='primary')
  template(v-else-if='text !== undefined')
    .row.q-gap-16.no-wrap.q-pt-18
      .col-auto
        q-avatar(color='primary-bg', text-color='white', size='36px')
          km-icon(:name='"magnet"', width='20', height='22')

      .col.border-radius-12.bg-light.q-pb-md
        //- .col-auto
        //-   .row.q-gap-16(style='height: 40px').q-pr-md.full-height
        //-     .col
        //-     .col-auto

        .q-py-16.q-px-24
          .km-paragraph.text-pre-wrap {{ text }}

        .row.justify-end.q-pr-md
          .col-auto
            km-btn(icon='fas fa-copy', iconColor='icon', iconSize='16px', size='sm', flat, contentClass='text-label', label='Copy', @click='copy')
</template>

<script>
import { ref } from 'vue'

export default {
  props: ['prompt', 'readonly'],
  emits: ['onLoad'],
  setup() {
    return {
      inputText: ref(''),
      text: ref(undefined),
    }
  },

  computed: {
    disabled() {
      return !this.inputText || this.loading
    },
    loading() {
      return this.$store.getters.enhancedTextLoading
    },
  },
  created() {},
  mounted() {},
  methods: {
    async submit() {
      this.text = (await this.$store.dispatch('enhanceText', { text: this.inputText, prompt: this.prompt.text })) || undefined
      this.$refs?.input.blur()
    },
  },
}
</script>

<style lang="stylus" scoped>
.circle-accent
  height: 16px
  width: 16px
  border-radius: 50%
  background: var(--q-primary)
  opacity: 0.5

.opaque
  opacity: 0.5
</style>
