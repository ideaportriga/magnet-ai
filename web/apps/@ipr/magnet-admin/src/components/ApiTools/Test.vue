<template>
  <div class="bg-white fit height-100 fit pb-3xl">
    <div class="flex-none">
      <div class="cluster mb-lg" data-justify="between">
        <div class="km-heading-7">{{ m.common_inputs() }}</div>
      </div>
    </div>
    <div v-for="formItem in form" :key="formItem.title" class="stack">
      <div class="km-table-chip km-small-chip text-black mb-sm">{{ formItem.title }}</div>
      <div v-if="!jsonMode" class="stack" data-gap="xs">
        <div v-for="field in formItem.fields" :key="field.name">
          <component :is="field.render.component" v-bind="field.render.props" v-model="formValues[formItem.title][field.name]" class="full-width" />
          <div class="km-description-2 text-secondary-text pb-xs pl-sm">{{ field.description ?? m.apiTools_noDescription() }}</div>
        </div>
      </div>
      <div v-else class="stack mb-lg" data-gap="xs">
        <km-codemirror v-model="jsonString[formItem.title]" :style="{ minHeight: &quot;150px&quot; }" :options="{ mode: &quot;application/json&quot; }" language="json" />
      </div>
    </div>
    <div class="cluster bb-border full-width" data-justify="end">
      <km-btn class="my-sm border-radius-6" unelevated padding="7px 8px" :disable="processing" @click="testApiTool">
        <template #default>
          <km-glyph name="send" size="16px" />
        </template>
      </km-btn>
    </div>
    <div class="flex-none mt-lg">
      <div class="cluster mb-xs" data-justify="between">
        <div class="km-heading-7">{{ m.common_outputs() }}</div>
      </div>
      <div v-if="response" class="stack" data-gap="xs">
        <km-codemirror v-if="response" v-model="response" :style="{ minHeight: &quot;150px&quot; }" :options="{ mode: &quot;application/json&quot; }" language="json" readonly />
      </div>
      <template v-if="!response &amp;&amp; processing">
        <div class="flex items-center justify-center" style="flex-direction: column">
          <km-loader size="62px" />
        </div>
      </template>
    </div>
  </div>
</template>
<script>
import { ref } from 'vue'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
export default {
  setup() {
    const { draft } = useEntityDetail('api_servers')
    const appStore = useAppStore()
    const formValues = ref({})
    const fields = ref({})
    return {
      draft,
      appStore,
      formValues,
      fields,
      m,
      jsonMode: ref(true),
      jsonString: ref({}),
      response: ref(null),
      processing: ref(false),
    }
  },
  computed: {
    apiTool() {
      return this.draft?.tools?.find((tool) => tool.system_name === this.$route.params.name)
    },

    properties() {
      return this.apiTool?.parameters?.input?.properties ?? {}
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
        tool: this.apiTool.system_name,
        variables: null,
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
      try {
        this.processing = true
        this.response = null
        const endpoint = this.appStore.config?.api?.aiBridge?.urlAdmin
        const response = await fetchData({
          endpoint,
          service: 'api_servers/call_tool',
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({
            server: this.draft?.system_name,
            tool: this.requestFromJson.tool,
            input_params: this.requestFromJson.input_params,
          }),
          headers: { 'Content-Type': 'application/json' },
        })
        const res = await response.text()
        this.response = JSON.stringify(JSON.parse(res), null, 2)
      } catch (error) {
      } finally {
        this.processing = false
      }
    },
  },
}
</script>
