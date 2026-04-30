<template>
  <km-dialog :model-value="showNewDialog" @cancel="$emit(&quot;cancel&quot;)" @hide="$emit(&quot;cancel&quot;)">
    <km-card class="card-style" style="min-inline-size: 800px">
      <div class="km-card-section card-section-style mb-md">
        <div class="cluster" data-justify="between">
          <div class="flex-1">
            <div class="km-heading-7">{{ m.apiServers_newApiTool() }}</div>
          </div>
          <div class="flex-none">
            <km-btn icon="close" flat dense @click="$emit(&quot;cancel&quot;)" />
          </div>
        </div>
      </div>
      <div class="km-card-section card-section-style mb-md">
        <div class="cluster" data-justify="center">
          <km-stepper class="full-width" :steps="[ { step: 0, description: &quot;Api spec&quot;, icon: &quot;pen&quot; }, { step: 1, description: &quot;Select API Tools&quot;, icon: &quot;circle&quot; }, ]" :stepper="stepper" />
        </div>
        <div v-if="stepper === 0" class="stack full-width">
          <div class="cluster full-width py-xs px-sm mb-lg bg-light" data-gap="sm" data-wrap="no">
            <km-glyph name="info" size="20px" style="min-inline-size: 20px" />
            <div class="km-paragraph pb-xs">Upload your API specification that may include one or multiple operations. You will be able to select which operations to convert to API tools in the next step.</div>
          </div>
          <div class="km-field text-secondary-text pb-xs pl-sm mt-lg pr-sm">API specification</div>
          <div style="--field-height: 40px">
            <km-file-picker v-model="file" class="km-control km-input rounded-borders" :multiple="false" max-files="1" rounded outlined :label="m.common_uploadFile()" accept=".json, .yaml" dense label-class="km-heading-2" />
            <div class="km-description-2 text-secondary-text pb-xs pl-sm">File format: JSON or YAML. Please make sure your API spec contains operation Ids and descriptions.</div>
          </div>
          <div class="km-field text-secondary-text pb-xs pl-sm mt-lg pr-sm">API specification Preview</div>
          <km-input v-model="actionsDefinition" type="textarea" rows="10" @input="actionsDefinition = $event" />
        </div>
        <div v-if="stepper === 1" class="stack full-width">
          <div class="cluster full-width py-xs px-sm mb-lg bg-light" data-gap="sm" data-wrap="no">
            <km-glyph name="info" size="20px" style="min-inline-size: 20px" />
            <div class="km-paragraph pb-xs">The following API Tools can be created from operations detected in the API Specification provided. Please select the API Tools you want to create.</div>
          </div>
          <div v-if="apiTools.some((tool) =&gt; tool.duplicate)" class="p-lg bg-warning-low">
            <div class="km-label">We have identified some API Tools that match existing API Tool names. What would you like to do with each of such tools?</div>
            <div class="stack pt-md" data-gap="lg">
              <km-radio v-model="addAsVariant" dense :val="false" label="Add as new tool" size="30px" />
            </div>
          </div>
          <div class="cluster p-lg">
            <km-checkbox size="40px" :model-value="allSelected" @update:model-value="updateAllTools" />
          </div>
          <template v-for="(tool, index) in apiTools" :key="index">
            <div class="py-sm px-lg bg-table-header bb-border">
              <km-checkbox class="mr-sm" :model-value="tool.selected === true" size="40px" @update:model-value="updateTool(index, $event)" />
              <div class="flex-1">
                <div class="cluster" data-justify="between">
                  <div class="km-button-text pb-xs">{{ tool.name }}</div>
                  <div v-if="tool.duplicate" class="cluster" data-gap="xs">
                    <km-glyph name="warning" tone="brand" size="14px" />
                    <div class="km-button-text text-primary km-description-2">Duplicate</div>
                  </div>
                </div>
                <div class="km-description text-secondary-text">{{ tool.description }}</div>
                <div class="km-description text-secondary-text">{{ !!tool.duplicate && addAsVariant ? `${tool.original_name} (${tool.duplicate})` : tool.system_name }}</div>
              </div>
            </div>
          </template>
        </div>
        <div class="cluster mt-lg" data-justify="between">
          <div class="flex-none">
            <km-btn flat :label="m.common_cancel()" tone="brand" @click="$emit(&quot;cancel&quot;)" />
          </div>
          <div class="flex-1" />
          <div class="flex-none">
            <template v-if="stepper === 0">
              <km-btn :label="m.common_next()" :disable="!readyForNext" @click="processFile" />
            </template>
            <template v-else>
              <km-btn :label="m.common_create()" @click="finish" />
            </template>
          </div>
        </div>
      </div>
    </km-card>
  </km-dialog>
</template>
<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { fetchData } from '@shared'
import { useEntityQueries } from '@/queries/entities'
import { useQueryClient } from '@tanstack/vue-query'
import _ from 'lodash'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useAppStore } from '@/stores/appStore'
export default {
  props: {
    showNewDialog: {
      default: false,
      type: Boolean,
    },
  },
  emits: ['cancel'],
  setup() {
    const queries = useEntityQueries()
    const queryClient = useQueryClient()
    const { draft, updateField } = useEntityDetail('api_servers')
    const appStore = useAppStore()

    return {
      file: ref(null),
      stepper: ref(0),
      apiTools: ref([]),
      addAsVariant: ref(false),
      actionsDefinition: ref(''),
      m,
      errorMessage: ref(null),
      appStore,
      queryClient,
      draft,
      updateField,
    }
  },
  computed: {
    readyForNext() {
      return !!this.actionsDefinition
    },
    allSelected() {
      return this.apiTools.every((tool) => tool.selected === true)
    },
    items() {
      return this.draft?.tools || []
    },
  },
  watch: {
    showNewDialog(newVal) {
      if (newVal) {
        this.apiTools = []
        this.file = null
        this.stepper = 0
        this.actionsDefinition = ''
        this.errorMessage = null
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
        const response = await fetchData({
          endpoint: this.appStore.config.api.aiBridge.urlAdmin,
          service: 'api_servers/parse_openapi_spec_text',
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ spec: text }),
        })
        if (response.error) throw response.error
        const res = await response.json()
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
      this.queryClient.invalidateQueries({ queryKey: ['api_servers'] })
    },
    async createTool(tools) {
      if (tools.length === 0) return
      const selectedTools = tools.map((tool) => {
        delete tool.selected
        delete tool.duplicate
        delete tool.original_name
        return tool
      })
      const currentTools = this.draft?.tools || []
      const allTools = [...currentTools, ...selectedTools]
      const id = this.draft?.id
      await fetchData({
        endpoint: this.appStore.config.api.aiBridge.urlAdmin,
        service: `api_servers/${id}`,
        method: 'PATCH',
        credentials: 'include',
        body: JSON.stringify({ tools: allTools }),
      })
      this.updateField('tools', allTools)
    },
    updateAllTools(value) {
      this.apiTools.forEach((tool) => {
        tool.selected = value
      })
    },
  },
}
</script>
