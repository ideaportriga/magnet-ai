<template lang="pug">
span
  codemirror.rounded-borders(
    :indent-with-tab='indentWithTab',
    :tab-size='tabSize',
    :modelValue='modelValue',
    @update:modelValue='$emit("update:modelValue", $event)',
    @change='$emit("update:modelValue", $event)',
    :style='{ minHeight: "200px", ...style }',
    :extensions='extensions',
    :disabled='readonly',
    :class='{ "bg-light": readonly }',
    :autofocus='false'
  )
  template(v-if='!!errorMessage')
    .km-small-chip.q-pa-4.q-pl-8.text-error-text {{ errorMessage }}
</template>
<script>
import { defineComponent, toRefs } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from '@codemirror/view'
import { json } from '@codemirror/lang-json'
import { python } from '@codemirror/lang-python'
import { useValidation, validationProps } from '@shared'

export default defineComponent({
  components: {
    Codemirror,
  },
  props: {
    modelValue: {},
    readonly: {
      default: false,
    },
    language: {
      type: String,
      default: 'json',
    },
    indentWithTab: {
      default: true,
    },
    tabSize: {
      default: 2,
    },
    style: {
      default: {},
    },
    ...validationProps(),
  },
  emits: ['update:modelValue'],
  setup(props) {
    let language = null
    switch (props.language.toLowerCase()) {
      case 'python':
        language = python()
        break
      case 'json':
        language = json()
        break
    }
    const extensions = [EditorView.lineWrapping, language]
    const { modelValue, rules } = toRefs(props)
    return {
      extensions,
      ...useValidation(modelValue, rules),
    }
  },
  computed: {
    selectedLineColor() {
      return this.readonly ? 'transparent' : '#cceeff44'
    },
  },
  methods: {},
})
</script>
<style lang="stylus">
.cm-gutters
    display: none !important;

.cm-editor
    margin: 1px
    border: 1px solid var(--q-border)
    border-radius: 4px;
    padding: 4px
    background: inherit
.cm-line{
    background: v-bind(selectedLineColor) !important//transparent !important
}
</style>
