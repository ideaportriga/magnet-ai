<template>
  <!-- eslint-disable vue/no-v-html -->
  <div>
    <div class="prompt-template-tab stack" data-gap="xs">
      <div class="prompt-template-tab__toolbar cluster" data-wrap="no">
        <div class="cluster full-width" data-gap="xs" data-justify="end">
          <km-btn flat round dense icon="code" icon-size="16px" :tone="viewMode === 'code' ? 'brand' : 'weak'" :tooltip="m.prompts_showRawTemplate()" @click="viewMode = 'code'" />
          <km-btn flat round dense icon="eye" icon-size="16px" :tone="viewMode === 'preview' ? 'brand' : 'weak'" :tooltip="m.prompts_showRenderedPreview()" @click="viewMode = 'preview'" />
        </div>
      </div>
      <!-- Preview: render as markdown with {vars} as chips-->
      <div v-if="viewMode === 'preview'" class="prompt-locked markdown-content">
        <div v-html="lockedRenderedHtml" />
      </div>
      <!-- Code: editable textarea-->
      <km-input v-else ref="input" v-model="text" rows="20" :placeholder="m.prompts_typeYourText()" border-radius="8px" height="36px" type="textarea" />
    </div>
  </div>
</template>

<script>
import { isEqual, orderBy, pickBy } from 'lodash'
import { m } from '@/paraglide/messages'
import { ref } from 'vue'
import MarkdownIt from 'markdown-it'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import chromaConfig from '@/config/entityFieldConfig'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const md = new MarkdownIt({ html: false, breaks: true })
    const { activeVariant, updateVariantField } = useVariantEntityDetail('promptTemplates')
    return {
      m,
      activeVariant,
      updateVariantField,
      markdownRenderer: md,
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
        return this.activeVariant?.text || ''
      },
      set(value) {
        this.updateVariantField('text', value)
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
      const res = {}
      Object.keys(chromaConfig).forEach((name) => {
        let controls = chromaConfig[name]?.config ?? {}
        controls = pickBy(controls, (o) => o.fieldName || o.dataType)
        controls = orderBy(Object.values(controls), ['label'])
        res[name] = { applet: chromaConfig[name], controls }
      })
      return res
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

<style scoped>
.prompt-template-tab {
  min-block-size: 0;
}

.prompt-template-tab__toolbar {
  min-block-size: 32px;
}

.prompt-locked {
  background: var(--ds-color-light);
  border-radius: var(--ds-radius-lg);
  padding: 12px 16px;
  min-block-size: 160px;
  font-size: var(--km-caption-size, 12px);
}
.prompt-locked :deep(.prompt-var-chip) {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  margin: 2px;
  border-radius: var(--ds-radius-sm);
  font-size: var(--km-caption-size, 12px);
  font-weight: 500;
  border: 1px solid var(--ds-color-primary);
  color: var(--ds-color-primary);
  background: transparent;
}
.prompt-locked :deep(p) {
  margin: 0 0 8px;
  line-height: 1.5;
}
.prompt-locked :deep(p:last-child) {
  margin-block-end: 0;
}
.prompt-locked :deep(ul),
.prompt-locked :deep(ol) {
  padding-inline-start: 20px;
  margin: 0 0 8px;
}
.prompt-locked :deep(table) {
  border-collapse: collapse;
  border: 1px solid var(--ds-color-border);
  margin: 0 0 8px;
  inline-size: auto;
  font-size: inherit;
}
.prompt-locked :deep(th),
.prompt-locked :deep(td) {
  border: 1px solid var(--ds-color-border);
  padding: 6px 10px;
  text-align: start;
  font-size: inherit;
}
.prompt-locked :deep(pre),
.prompt-locked :deep(code) {
  background: var(--ds-color-border-2);
  border-radius: var(--ds-radius-sm);
  padding: 2px 6px;
  font-size: var(--km-caption-size, 12px);
}
.prompt-locked :deep(pre) {
  padding: 12px;
  overflow-inline: auto;
  white-space: pre-wrap;
}
.prompt-locked :deep(h1),
.prompt-locked :deep(h2),
.prompt-locked :deep(h3),
.prompt-locked :deep(h4),
.prompt-locked :deep(h5),
.prompt-locked :deep(h6) {
  margin: 12px 0 6px;
  line-height: 1.3;
  font-size: 1.5em;
  font-weight: 600;
}
.prompt-locked :deep(h2) {
  font-size: 1.33em;
}
.prompt-locked :deep(h3) {
  font-size: 1.25em;
}
.prompt-locked :deep(h4) {
  font-size: 1.17em;
}
.prompt-locked :deep(h5) {
  font-size: 1.08em;
}
.prompt-locked :deep(h6) {
  font-size: 1em;
}
.prompt-locked :deep(h1:first-child),
.prompt-locked :deep(h2:first-child),
.prompt-locked :deep(h3:first-child),
.prompt-locked :deep(h4:first-child) {
  margin-block-start: 0;
}
.prompt-locked :deep(strong) {
  font-weight: 600;
}
.prompt-locked :deep(a) {
  color: var(--ds-color-primary);
  text-decoration: none;
}
.prompt-locked :deep(a:hover) {
  text-decoration: underline;
}
</style>
