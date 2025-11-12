<template lang="pug">
q-dialog(:model-value='showNewDialog', @cancel='$emit("cancel")', @hide='$emit("cancel")')
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
          :steps='[ { step: 0, description: "Api spec", icon: "pen" }, { step: 1, description: "Select API Tools", icon: "circle" }, ]',
          :stepper='stepper'
        )
      .column.full-width(v-if='stepper === 0')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 Upload your API specification that may include one or multiple operations. You will be able to select which operations to convert to API tools in the next step.

        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg.q-pr-8 API specification
        div(style='--field-height: 40px')
          q-file.km-control.km-input.rounded-borders(
            :multiple='false',
            max-files='1',
            rounded,
            outlined,
            label='Upload File',
            v-model='file',
            accept='.json, .yaml',
            dense,
            labelClass='km-heading-2'
          )
          .km-description-2.text-secondary-text.q-pb-4.q-pl-8 File format: JSON or YAML. Please make sure your API spec contains operation Ids and descriptions.
        .km-field.text-secondary-text.q-pb-xs.q-pl-8.q-mt-lg.q-pr-8 API specification Preview
        km-input(v-model='actionsDefinition', type='textarea', rows='10')
      .column.full-width(v-if='stepper === 1')
        .row.bg-light.full-width.q-py-4.q-px-8.q-gap-8.no-wrap.items-center.q-mb-lg
          q-icon(name='o_info', color='icon', size='20px', style='min-width: 20px')
          .km-paragraph.q-pb-4 The following API Tools can be created from operations detected in the API Specification provided. Please select the API Tools you want to create.

        .row.bg-warning-low.q-pa-16(v-if='apiTools.some((tool) => tool.duplicate)')
          .km-label We have identified some API Tools that match existing API Tool names. What would you like to do with each of such tools?
          .column.q-pt-md.q-gap-16
            //- q-radio(dense, v-model='addAsVariant', :val='true', label='Add as tool variant', size='30px')
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
    const { ...useApiServers } = useChroma('api_servers')

    return {
      file: ref(null),
      stepper: ref(0),
      apiTools: ref([]),
      addAsVariant: ref(false),
      actionsDefinition: ref(''),
      errorMessage: ref(null),
      store,
      useApiServers,
    }
  },
  computed: {
    readyForNext() {
      return !!this.file
    },
    allSelected() {
      return this.apiTools.every((tool) => tool.selected === true)
    },
    items() {
      return this.store.getters.api_server?.tools || []
    },
  },
  watch: {
    showNewDialog(newVal) {
      if (newVal) {
        this.apiTools = []
        this.file = null
        this.stepper = 0
      }
    },
    async file(newVal) {
      if (newVal) {
        this.actionsDefinition = await this.readFileAsText(newVal)
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
    readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = (err) => reject(err)
        reader.readAsText(file)
      })
    },
    async processFile() {
      const text = this.actionsDefinition || (await this.readFileAsText(this.file))
      try {
        const res = await this.store.dispatch('specFromText', text)
        res?.tools?.forEach((tool) => {
          tool.original_name = tool.system_name
          tool.duplicate = this.isDuplicate(tool.system_name)
          tool.system_name = this.uniqueSystemName(tool.system_name)

          tool.selected = true
        })
        this.apiTools = res?.tools || []
        this.proceed()
      } catch (error) {
        this.errorMessage = error
      }
    },
    isDuplicate(name) {
      const originalName = name
      const duplicate = this.items.find((item) => item.system_name === originalName)
      // if (duplicate) {
      //   return `variant_${duplicate.variants.length + 1}`
      // }
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
      await this.createTool(selectedTools)
      this.$emit('cancel')
      this.useApiServers.get()
    },
    async createTool(tools) {
      if (tools.length === 0) return
      const selectedTools = tools.map((tool) => {
        delete tool.selected
        delete tool.duplicate
        delete tool.original_name
        return tool
      })
      await this.store.dispatch('addTools', selectedTools)
    },
    updateAllTools(value) {
      this.apiTools.forEach((tool) => {
        tool.selected = value
      })
    },
  },
}
</script>
