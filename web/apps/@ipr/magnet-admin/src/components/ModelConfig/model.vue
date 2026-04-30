<template>
  <div>
    <km-section title="Model configuration" sub-title="Foundational model settings">
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        Provider
        <km-select ref="providerRef" v-model="provider" height="auto" min-height="30px" :placeholder="m.common_provider()" :options="providerItems" emit-value map-options option-value="id" />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        {{ m.common_type() }}
        <km-select ref="typeRef" v-model="type" height="auto" min-height="30px" :placeholder="m.common_type()" :options="categoryOptions" emit-value map-options />
      </div>
      <div class="km-field text-secondary-text pb-xs pl-sm mb-md">
        Name
        <div class="full-width">
          <km-input ref="modelRef" v-model="model" height="30px" :placeholder="m.placeholder_exampleModelId()" />
        </div>
      </div>
    </km-section>
    <km-separator v-if="type === &quot;prompts&quot;" class="my-lg" />
    <km-section v-if="type === &quot;prompts&quot;" title="Structured data support" sub-title="Model specific features">
      <div class="basis-6 km-field text-secondary-text pb-xs pl-sm">
        <div class="cluster">
          <km-toggle ref="json_modeRef" v-model="json_mode" height="30px" :placeholder="m.placeholder_exampleModelName()" />
          <div class="km-field text-secondary-text">JSON mode</div>
        </div>
      </div>
      <div class="basis-6 km-field text-secondary-text pb-xs pl-sm">
        <div class="cluster">
          <km-toggle ref="json_schemaRef" v-model="json_schema" height="30px" :placeholder="m.placeholder_exampleModelName()" />
          <div class="km-field text-secondary-text">JSON schema</div>
        </div>
      </div>
      <div class="basis-6 km-field text-secondary-text pb-xs pl-sm">
        <div class="cluster">
          <km-toggle ref="json_schemaRef" v-model="tool_calling" height="30px" :placeholder="m.placeholder_exampleModelName()" />
          <div class="km-field text-secondary-text">Tool calling</div>
        </div>
      </div>
      <div class="basis-6 km-field text-secondary-text pb-xs pl-sm">
        <div class="cluster">
          <km-toggle ref="json_schemaRef" v-model="reasoning" height="30px" :placeholder="m.placeholder_exampleModelName()" />
          <div class="km-field text-secondary-text">Reasoning</div>
        </div>
      </div>
    </km-section>
    <km-separator class="my-lg" />
    <km-section title="Additional information" sub-title="Useful information about the model">
      <div class="cluster">
        <div class="flex-1 km-field text-secondary-text pb-xs pl-sm mb-md">
          Resources
          <div class="full-width">
            <km-input ref="resourcesRef" rows="10" :placeholder="m.placeholder_typeYourTextHere()" :model-value="resources" border-radius="8px" height="36px" type="textarea" @input="resources = $event" />
          </div>
        </div>
      </div>
    </km-section>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { m } from '@/paraglide/messages'
import { useEntityQueries } from '@/queries/entities'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { categoryOptions } from '@/config/model/model.js'
export default {
  props: [],
  emits: [],

  setup() {
    const queries = useEntityQueries()
    const { draft, updateField } = useEntityDetail('model')
    const { data: providerData } = queries.provider.useList()
    const providerItems = computed(() => providerData.value?.items ?? [])

    return {
      m,
      draft,
      updateField,
      providerItems,
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
      categoryOptions,
    }
  },
  computed: {
    provider: {
      get() {
        return this.draft?.provider || ''
      },
      set(value) {
        this.updateField('provider', value)
      },
    },
    model: {
      get() {
        return this.draft?.ai_model || ''
      },
      set(value) {
        this.updateField('ai_model', value)
      },
    },
    json_mode: {
      get() {
        return this.draft?.json_mode || false
      },
      set(value) {
        this.updateField('json_mode', value)
      },
    },
    json_schema: {
      get() {
        return this.draft?.json_schema || false
      },
      set(value) {
        this.updateField('json_schema', value)
      },
    },
    tool_calling: {
      get() {
        return this.draft?.tool_calling || false
      },
      set(value) {
        this.updateField('tool_calling', value)
      },
    },
    reasoning: {
      get() {
        return this.draft?.reasoning || false
      },
      set(value) {
        this.updateField('reasoning', value)
      },
    },
    price_input_unit_name: {
      get() {
        return this.draft?.price_input_unit_name || ''
      },
      set(value) {
        this.updateField('price_input_unit_name', value)
      },
    },
    price_standard_input: {
      get() {
        return this.draft?.price_input || ''
      },
      set(value) {
        this.updateField('price_input', parseFloat(value))
      },
    },
    price_standard_input_unit_count: {
      get() {
        return this.draft?.price_standard_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_input_unit_count', parseFloat(value))
      },
    },
    price_cached_input: {
      get() {
        return this.draft?.price_cached || ''
      },
      set(value) {
        this.updateField('price_cached', parseFloat(value))
      },
    },
    price_cached_input_unit_count: {
      get() {
        return this.draft?.price_cached_input_unit_count || ''
      },
      set(value) {
        this.updateField('price_cached_input_unit_count', parseFloat(value))
      },
    },
    price_output_unit_name: {
      get() {
        return this.draft?.price_output_unit_name || ''
      },
      set(value) {
        this.updateField('price_output_unit_name', value)
      },
    },
    price_standard_output: {
      get() {
        return this.draft?.price_output || ''
      },
      set(value) {
        this.updateField('price_output', parseFloat(value))
      },
    },
    price_standard_output_unit_count: {
      get() {
        return this.draft?.price_standard_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_standard_output_unit_count', parseFloat(value))
      },
    },
    price_reasoning_output: {
      get() {
        return this.draft?.price_reasoning || ''
      },
      set(value) {
        this.updateField('price_reasoning', parseFloat(value))
      },
    },
    price_reasoning_output_unit_count: {
      get() {
        return this.draft?.price_reasoning_output_unit_count || ''
      },
      set(value) {
        this.updateField('price_reasoning_output_unit_count', parseFloat(value))
      },
    },
    resources: {
      get() {
        return this.draft?.resources || ''
      },
      set(value) {
        this.updateField('resources', value)
      },
    },
    type: {
      get() {
        return this.draft?.type || ''
      },
      set(value) {
        this.updateField('type', value)
      },
    },
  },
  created() {},
  methods: {},
}
</script>
