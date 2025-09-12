<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")')
  q-card.card-style(style='min-width: 800px')
    q-card-section.card-section-style.q-mb-md
      .row
        .col
          .km-heading-7 New API Tool
        .col-auto
          q-btn(icon='close', flat, dense, @click='$emit("cancel")')
    q-card-section.card-section-style.q-mb-md
      .row.items-center.justify-center
        km-stepper.full-width(
          :steps='[ { step: 0, description: "Upload spec", icon: "pen" }, { step: 1, description: "Select API Tools", icon: "circle" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 Upload your API specification that may include one or multiple operations. You will be able to select which operations to convert to API tools in the next step.
        .km-field.text-secondary-text.q-pb-xs.q-pl-8 API provider
        km-select(height='auto', placeholder='API Provider', v-model='model', :options='apiProviderOptions', emit-value)

        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg.q-pr-8 API specification
        div(style='--field-height: 40px')
          q-file.km-control.km-input.rounded-borders(
            :multiple='false',
            max-files='1',
            rounded,
            outlined,
            label='Upload Files',
            v-model='file',
            accept='.json, .yaml',
            dense,
            labelClass='km-heading-2'
          )
          .km-description-2.text-secondary-text.q-pb-4.q-pl-8 File format: JSON or YAML. Please make sure your API spec contains operation Ids and descriptions.
      .column.full-width(v-if='stepper === 1')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 The following API Tools can be created from operations detected in the API Specification provided. Please select the API Tools you want to create.

        .row.bg-warning-low.q-pa-16(v-if='apiTools.some((tool) => tool.duplicate)')
          .km-label We have identified some API Tools that match existing API Tool names. What would you like to do with each of such tools?
          .column.q-pt-md.q-gap-16
            q-radio(dense, v-model='addAsVariant', :val='true', label='Add as tool variant', size='30px')
            q-radio(dense, v-model='addAsVariant', :val='false', label='Add as new tool', size='30px')
        .row.q-pa-16.items-center
          km-checkbox(size='40px', :model-value='allSelected', @update:model-value='updateAllTools')
          //- .km-paragraph {{ allSelected ? 'Deselect all' : 'Select all' }}

        template(v-for='(tool, index) in apiTools') 
          .row.q-py-8.q-px-16.bg-table-header.bb-border
            km-checkbox.q-mr-sm(:model-value='tool.selected === true', @update:model-value='updateTool(index, $event)', size='40px')
            .col
              .row.items-center.justify-between
                .km-button-text.q-pb-4 {{ tool.name }}
                .row.q-gap-4.items-center(v-if='tool.duplicate')
                  q-icon(name='warning', color='primary', size='14px')
                  .km-button-text.text-primary.km-description-2 Duplicate
              .km-description.text-secondary-text {{ tool.description }}
              .km-description.text-secondary-text {{ !!tool.duplicate && addAsVariant ? `${tool.original_name} (${tool.duplicate})` : tool.system_name }}
      .row.q-mt-lg
        .col-auto
          km-btn(flat, label='Cancel', color='primary', @click='$emit("cancel")')
        .col
        .col-auto
          template(v-if='stepper === 0')
            km-btn(label='Next', @click='processFile', :disable='!readyForNext')
          template(v-else)
            km-btn(label='Create', @click='finish')
</template>
<script>
import { ref, computed } from 'vue'
import { fetchData } from '@shared'
import { useStore } from 'vuex'
import { useChroma } from '@shared'
import _ from 'lodash'
export default {
  props: {
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup() {
    const store = useStore()
    const { items, ...useApiTools } = useChroma('api_tools')
    const { items: apiProviders } = useChroma('api_tool_providers')

    const apiProviderOptions = computed(() => {
      return apiProviders.value.map((apiProvider) => ({
        label: apiProvider.systemName,
        value: apiProvider.systemName,
      }))
    })

    return {
      file: ref(null),
      model: ref(''),
      stepper: ref(0),
      apiTools: ref([]),
      addAsVariant: ref(false),
      store,
      items,
      useApiTools,
      apiProviderOptions,
    }
  },
  computed: {
    readyForNext() {
      return !!this.file && !!this.model
    },
    allSelected() {
      return this.apiTools.every((tool) => tool.selected === true)
    },
  },
  watch: {
    showNewDialog(newVal) {
      if (newVal) {
        this.apiTools = []
        this.file = null
        this.model = null
        this.stepper = 0
      }
    },
  },

  methods: {
    updateTool(index, value) {
      Object.assign(this.apiTools[index], { selected: value })
    },
    proceed() {
      this.stepper++
    },
    async processFile() {
      const body = new FormData()
      body.append('file', this.file)
      const response = await fetchData({
        endpoint: this.store.getters.config.api.aiBridge.urlAdmin,
        service: `api_tools/generate_from_openapi`,

        method: 'POST',
        credentials: 'include',
        // headers: {
        //   'Content-Type': 'multipart/form-data'
        // },
        body,
      })
      if (response?.error) {
        console.log(response?.error)
      } else {
        const res = await response.json()
        res.forEach((tool) => {
          tool.original_name = tool.system_name
          tool.duplicate = this.isDuplicate(tool.system_name)
          tool.system_name = this.uniqueSystemName(tool.system_name)

          tool.selected = true
        })
        this.apiTools = res
        console.log(res)
        this.proceed()
      }
    },
    isDuplicate(name) {
      const originalName = name
      const duplicate = this.items.find((item) => item.system_name === originalName)
      if (duplicate) {
        return `variant_${duplicate.variants.length + 1}`
      }
      return false
    },
    uniqueSystemName(name) {
      let i = 0
      const originalName = name
      name = originalName
      while (this.items.some((item) => item.system_name === name)) {
        i++
        name = `${originalName}_${i}`
      }
      return name
    },
    async finish() {
      const selectedTools = this.apiTools.filter((tool) => tool.selected === true)
      if (!this.addAsVariant) {
        await this.createTool(selectedTools)
      } else {
        const existingTools = selectedTools.filter((tool) => tool.duplicate)
        const newTools = selectedTools.filter((tool) => !tool.duplicate)
        await this.duplicateTool(existingTools)
        await this.createTool(newTools)
      }
      this.$emit('cancel')
      this.useApiTools.get()
    },
    async createTool(tools) {
      if (tools.length === 0) return
      const selectedTools = tools.map((tool) => {
        delete tool.selected
        delete tool.duplicate
        delete tool.original_name
        tool['api_provider'] = this.model
        return tool
      })
      await fetchData({
        endpoint: this.store.getters.config.api.aiBridge.urlAdmin,
        service: `sql_api_tools/bulk`,
        method: 'POST',
        credentials: 'include',
        body: JSON.stringify(selectedTools),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    },
    async duplicateTool(tools) {
      if (tools.length === 0) return
      tools.forEach((tool) => {
        const parent = this.items.find((item) => item.system_name === tool.original_name)
        const variant = tool.variants[0]
        variant.variant = `variant_${parent.variants.length + 1}`
        const updatedTool = {
          ...parent,
          variants: [...parent.variants, variant],
        }
        console.log(updatedTool)
        this.$store.dispatch('chroma/update', { payload: { id: parent.id, data: updatedTool }, entity: 'api_tools' })
      })
    },
    updateAllTools(value) {
      this.apiTools.forEach((tool) => {
        tool.selected = value
      })
    },
  },
}
</script>
