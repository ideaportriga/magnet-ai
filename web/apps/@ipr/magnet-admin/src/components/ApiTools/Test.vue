<template lang="pug">
.bg-white.fit.height-100.fit.q-pb-32
  .col-auto
    .row.items-center.justify-between
      .km-heading-7.q-mb-16 Inputs
  //-     km-checkbox(v-model="jsonMode" label="JSON mode")
  .column(v-for='form in form')
    .row
      .row.km-table-chip.km-small-chip.text-black.q-mb-8 {{ form.title }}
    .column.q-gap-4(v-if='!jsonMode')
      .row(v-for='field in form.fields')
        component.full-width(:is='field.render.component', v-bind='field.render.props', v-model='formValues[form.title][field.name]')
        .km-description-2.text-secondary-text.q-pb-4.q-pl-8 {{ field.description ?? 'No description' }}
    .column.q-gap-4.q-mb-16(v-else)
      km-codemirror(v-model='jsonString[form.title]', :style='{ minHeight: "150px" }', :options='{ mode: "application/json" }', language='json')
  .row.justify-end.bb-border.full-width
    q-btn.q-my-6.border-radius-6(color='primary', @click='testApiTool', unelevated, padding='7px 8px')
      template(v-slot:default)
        q-icon(name='fas fa-paper-plane', size='16px')
  .col-auto.q-mt-lg
    .row.items-center.justify-between
      .km-heading-7.q-mb-xs Outputs
    .column.q-gap-4
      km-codemirror(
        v-if='response',
        v-model='response',
        :style='{ minHeight: "150px" }',
        :options='{ mode: "application/json" }',
        language='json',
        readonly
      )
</template>
<script>
import { ref } from 'vue'
export default {
  setup() {
    const formValues = ref({})
    const fields = ref({})
    return {
      formValues,
      fields,
      jsonMode: ref(true),
      jsonString: ref({}),
      response: ref(null),
    }
  },
  computed: {
    apiTool() {
      return this.$store.getters.api_tool ?? {}
    },
    apiToolVariant() {
      return this.$store.getters.api_tool_variant ?? {}
    },
    properties() {
      return this.apiToolVariant?.value?.parameters?.input?.properties ?? {}
    },
    sections() {
      return Object.keys(this.properties ?? {})
    },
    form() {
      return this.sections.map((section) => {
        const fields = this.properties[section].properties
        return {
          title: section,
          fields: this.generateFormFields(fields, section),
        }
      })
    },
    requestFromJson() {
      return {
        api_tool_config: {
          api_provider: this.apiTool.api_provider,
          path: this.apiTool.path,
          method: this.apiTool.method,
          mock: this.apiTool.mock,
        },
        input_params: {
          queryParams: JSON.parse(this.jsonString.queryParams ?? '{}'),
          requestBody: JSON.parse(this.jsonString.requestBody ?? '{}'),
          pathParams: JSON.parse(this.jsonString.pathParams ?? '{}'),
        },
      }
    },
  },
  watch: {
    form: {
      handler(newVal) {
        this.generateFormValues(newVal)
      },
      deep: true,
      immediate: true,
    },
  },
  methods: {
    generateFormValues(form) {
      if (!form?.length) return
      const jsonString = {}
      form.forEach((section) => {
        section.fields.forEach((field) => {
          if (!this.formValues[section.title]) this.formValues[section.title] = {}
          this.formValues[section.title][field.name] = ''
          if (!this.fields[section.title]) this.fields[section.title] = []
          this.fields[section.title] = [...this.fields[section.title], field.name]

          if (field.required) {
            let value = ''
            if (field.type === 'boolean') value = true
            if (field.type === 'array') value = []
            if (field.type === 'object') value = {}
            if (field.enum) value = field.enum[0]
            jsonString[section.title] = { ...jsonString[section.title], [field.name]: value }
          }
        })
      })

      Object.keys(jsonString).forEach((section) => {
        jsonString[section] = JSON.stringify(jsonString[section], null, 2)
      })
      this.jsonString = jsonString
    },
    generateFormFields(fields, section) {
      if (!fields) return []
      return Object.keys(fields).map((field) => {
        // if (!this.formValues[section]) this.formValues[section] = {}
        // this.formValues[section][field] = ''
        // if (!this.fields[section]) this.fields[section] = []
        // this.fields[section] = [...this.fields[section], field]
        return {
          name: field,
          render: this.getComponentAndProps(fields[field], field),
          required: (this.properties[section]?.required || []).includes(field),
          ...fields[field],
        }
      })
    },
    getComponentAndProps(field, name) {
      if (field.enum && (field.type === 'string' || field.type === 'array')) {
        return {
          component: 'km-select',
          props: {
            options: field.enum,
            multiple: field.type === 'array',
          },
        }
      }
      if (field.type === 'string') {
        return {
          component: 'km-input',
          props: {
            placeholder: name,
          },
        }
      }
      if (field.type === 'number' || field.type === 'integer') {
        return {
          component: 'km-input',
          props: {
            placeholder: name,
            type: 'number',
          },
        }
      }
      if (field.type === 'boolean') {
        return {
          component: 'km-checkbox',
          props: {
            label: name,
            class: 'items-center',
          },
        }
      }
      if (field.type === 'object') {
        return {
          component: 'km-codemirror',
          props: {
            placeholder: name,
          },
        }
      }
      return {
        component: 'km-input',
        props: {
          placeholder: name,
        },
      }
    },
    async testApiTool() {
      const res = await this.$store.dispatch('testApiTool', this.requestFromJson)
      this.response = JSON.stringify(JSON.parse(res.content), null, 2)
    },
  },
}
</script>
