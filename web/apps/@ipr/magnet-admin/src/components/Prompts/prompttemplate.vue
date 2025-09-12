<template lang="pug">
div
  km-section(title='Prompt template', subTitle='Template of instructions to be sent to the LLM')
    .km-field.text-secondary-text.q-pb-xs.q-pl-8 Prompt template body
    km-input(ref='input', rows='20', placeholder='Type your text here', border-radius='8px', height='36px', type='textarea', v-model='text')
  q-separator.q-my-lg
</template>

<script>
import { isEqual, orderBy, pickBy } from 'lodash'
import { ref } from 'vue'
import { useChroma } from '@shared'

export default {
  props: ['prompt', 'selectedRow'],
  emits: ['setProp', 'save', 'cancel', 'remove', 'openTest'],

  setup() {
    const { publicItems, publicSelected, publicSelectedOptionsList } = useChroma('collections')
    return {
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
  computed: {
    text: {
      get() {
        return this.$store.getters.promptTemplateVariant?.text || ''
      },
      set(value) {
        this.$store.commit('updateNestedPromptTemplateProperty', { path: 'text', value })
      },
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
