<template lang="pug">
<!-- eslint-disable vue/no-v-html -->
div
  div
    .row.items-center.q-px-8.q-pb-xs
      //- .col.km-field.text-secondary-text Prompt template body
      .row.items-center.q-gutter-xs.justify-end.full-width
        q-btn(
          flat
          round
          dense
          icon='code'
          :color="viewMode === 'code' ? 'primary' : 'grey-5'"
          @click="viewMode = 'code'"
        )
          q-tooltip.bg-white.block-shadow.km-description.text-text-grey Show raw template
        q-btn(
          flat
          round
          dense
          icon='visibility'
          :color="viewMode === 'preview' ? 'primary' : 'grey-5'"
          @click="viewMode = 'preview'"
        )
          q-tooltip.bg-white.block-shadow.km-description.text-text-grey Show rendered preview

    // Preview: render as markdown with {vars} as chips
    div.q-px-8.q-pt-sm.prompt-locked.markdown-content(v-if="viewMode === 'preview'")
      div(v-html="lockedRenderedHtml")

    // Code: editable textarea
    km-input(
      v-else
      ref='input'
      rows='20'
      placeholder='Type your text here'
      border-radius='8px'
      height='36px'
      type='textarea'
      v-model='text'
    )
  q-separator.q-my-lg
</template>

<script>
import { isEqual, orderBy, pickBy } from 'lodash'
import { ref } from 'vue'
import { useChroma } from '@shared'
import MarkdownIt from 'markdown-it'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const { publicItems, publicSelected, publicSelectedOptionsList } = useChroma('collections')
    const md = new MarkdownIt({ html: false, breaks: true })
    return {
      markdownRenderer: md,
      publicItems,
      publicSelected,
      publicSelectedOptionsList,
      test: ref(true),
      iconPicker: ref(false),
      showError: ref(false),
      selectedEntity: ref(),
      promptInput: ref(null),
      llm: ref(true),
      semanticCache: ref(false),
      semanticCacheChoice: ref('faq'),
    }
  },

  data() {
    return {
      // 'preview' | 'code'
      viewMode: 'preview',
    }
  },
  computed: {
    text: {
      get() {
        return this.$store.getters.promptTemplateVariant?.text || ''
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'text', value })
      },
    },

    parsedSegments() {
      const input = this.text || ''
      const segments = []
      const varRegex = /\{[A-Za-z_][A-Za-z0-9_]*\}/g

      let lastIndex = 0
      let match

      while ((match = varRegex.exec(input)) !== null) {
        const start = match.index
        const end = varRegex.lastIndex

        if (start > lastIndex) {
          segments.push({
            type: 'text',
            value: input.slice(lastIndex, start),
          })
        }

        const varName = match[0].slice(1, -1)
        segments.push({
          type: 'var',
          value: varName,
        })

        lastIndex = end
      }

      if (lastIndex < input.length) {
        segments.push({
          type: 'text',
          value: input.slice(lastIndex),
        })
      }

      return segments
    },

    // Markdown-rendered text for locked mode, with {vars} as chip-style spans
    lockedRenderedHtml() {
      const input = this.text || ''
      const varRegex = /\{[A-Za-z_][A-Za-z0-9_]*\}/g
      const vars = []
      const textForMd = input.replace(varRegex, (match) => {
        const varName = match.slice(1, -1)
        const idx = vars.length
        vars.push(varName)
        return `\u200B__VAR${idx}__\u200B`
      })
      let html = this.markdownRenderer.render(textForMd)
      vars.forEach((varName, idx) => {
        const placeholder = `\u200B__VAR${idx}__\u200B`
        const escaped = varName.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
        const chipHtml = `<span class="prompt-var-chip">${escaped}</span>`
        html = html.split(placeholder).join(chipHtml)
      })
      return html
    },
    hasChanges() {
      if (this.selectedRow?.id !== undefined) return !isEqual(this.prompt, this.selectedRow)
      else return true
    },
    hasError() {
      return !(this.prompt.name && this.prompt.text && this.prompt.description)
    },
    isNew() {
      return this.prompt && this.prompt.id === undefined
    },
    canSave() {
      return !!this.prompt.text && !!this.prompt.description && !!this.prompt.name
    },

    promptMetadata() {
      const views = this.$store.getters.views
      return Object.values(views).reduce((res, { entities }) => {
        Object.keys(entities).forEach((name) => {
          let controls = this.$store.getters.controls?.[name] ?? {}
          controls = pickBy(controls, (o) => o.fieldName || o.dataType)
          controls = orderBy(controls, ['label'])

          res[name] = { applet: entities[name], controls }
        })
        return res
      }, {})
    },

    metadataFields() {
      return this.promptMetadata[this.selectedEntity]?.controls ?? {}
    },
  },
  created() {},
  methods: {
    setProp(name, val) {
      this.$emit('setProp', { name, val })
    },
    save() {
      if (this.hasError) {
        this.showError = true
        return
      }
      this.showError = false
      this.$emit('save')
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`/${path}`)
      }
    },
  },
}
</script>

<style lang="stylus" scoped>
.prompt-locked
  background: #f7f7f9
  border-radius: 8px
  padding: 12px 16px
  min-height: 160px
  // Align with km-description (12px) from base typography
  font-size: 12px

.prompt-locked :deep(.prompt-var-chip)
  display: inline-flex
  align-items: center
  padding: 2px 8px
  margin: 2px 2px
  border-radius: 4px
  font-size: 12px
  font-weight: 500
  border: 1px solid var(--q-primary)
  color: var(--q-primary)
  background: transparent

.prompt-locked :deep(p)
  margin: 0 0 8px 0
  line-height: 1.5

.prompt-locked :deep(p:last-child)
  margin-bottom: 0

.prompt-locked :deep(ul),
.prompt-locked :deep(ol)
  padding-left: 20px
  margin: 0 0 8px 0

.prompt-locked :deep(table)
  border-collapse: collapse
  border: 1px solid rgba(0, 0, 0, 0.12)
  margin: 0 0 8px 0
  width: auto
  font-size: inherit

.prompt-locked :deep(th),
.prompt-locked :deep(td)
  border: 1px solid rgba(0, 0, 0, 0.12)
  padding: 6px 10px
  text-align: left
  font-size: inherit

.prompt-locked :deep(pre),
.prompt-locked :deep(code)
  background: rgba(0, 0, 0, 0.06)
  border-radius: 4px
  padding: 2px 6px
  font-size: 12px

.prompt-locked :deep(pre)
  padding: 12px
  overflow-x: auto
  white-space: pre-wrap

.prompt-locked :deep(h1),
.prompt-locked :deep(h2),
.prompt-locked :deep(h3),
.prompt-locked :deep(h4),
.prompt-locked :deep(h5),
.prompt-locked :deep(h6)
  margin: 12px 0 6px 0
  line-height: 1.3
  // Keep headings modest; at most +6px over body
  font-size: 18px
  font-weight: 600

.prompt-locked :deep(h2)
  font-size: 16px

.prompt-locked :deep(h3)
  font-size: 15px

.prompt-locked :deep(h4)
  font-size: 14px

.prompt-locked :deep(h5)
  font-size: 13px

.prompt-locked :deep(h6)
  font-size: 12px

.prompt-locked :deep(h1:first-child),
.prompt-locked :deep(h2:first-child),
.prompt-locked :deep(h3:first-child),
.prompt-locked :deep(h4:first-child)
  margin-top: 0

.prompt-locked :deep(strong)
  font-weight: 600

.prompt-locked :deep(a)
  color: var(--q-primary)
  text-decoration: none

.prompt-locked :deep(a:hover)
  text-decoration: underline
</style>
