<template>
  <div>
    <km-section title="Pricing" sub-title="Pricing information about the model">
      <div class="cluster mb-md" data-gap="lg">
        <div class="stack">
          <div class="km-field text-secondary-text pl-sm mb-sm pricing__label">
            Input units
            <km-select v-model="price_input_unit_name" height="auto" min-height="30px" :options="priceUnitOptions" map-options emit-value option-value="value" option-label="label" />
          </div>
        </div>
        <div class="stack">
          <div class="cluster full-width" data-gap="lg">
            <div class="km-field text-secondary-text pl-sm mb-sm">
              Price for {{ type === 'prompts' ? 'standard' : '' }} input {{ price_input_unit_name }}
              <km-input v-model="price_standard_input" prefix="$" height="32px" class="pricing__amount-input" />
            </div>
            <div class="text-secondary-text mt-xs">per</div>
            <km-input v-model="price_standard_input_unit_count" class="mt-sm pricing__count-input" height="32px" />
            <div class="text-secondary-text mt-xs">{{ price_input_unit_name }}</div>
          </div>
          <div v-if="type === &quot;prompts&quot;" class="cluster full-width" data-gap="lg">
            <div class="km-field text-secondary-text pl-sm mb-sm">
              Price for cached input {{ price_input_unit_name }}
              <km-input v-model="price_cached_input" prefix="$" height="32px" class="pricing__amount-input" />
            </div>
            <div class="text-secondary-text mt-xs">per</div>
            <km-input v-model="price_cached_input_unit_count" class="mt-sm pricing__count-input" height="32px" />
            <div class="text-secondary-text mt-xs">{{ price_input_unit_name }}</div>
          </div>
        </div>
      </div>
      <div v-if="type === &quot;prompts&quot;" class="cluster mb-md" data-gap="lg">
        <div class="stack">
          <div class="km-field text-secondary-text pl-sm mb-sm pricing__label">
            Output units
            <km-select v-model="price_output_unit_name" height="auto" min-height="30px" :options="priceUnitOptions" map-options emit-value option-value="value" option-label="label" />
          </div>
        </div>
        <div class="stack">
          <div class="cluster full-width" data-gap="lg">
            <div class="km-field text-secondary-text pl-sm mb-sm">
              Price for {{ type === 'prompts' ? 'standard' : '' }} output {{ price_output_unit_name }}
              <km-input v-model="price_standard_output" prefix="$" height="30px" class="pricing__amount-input" />
            </div>
            <div class="text-secondary-text">per</div>
            <km-input v-model="price_standard_output_unit_count" height="32px" class="pricing__count-input" />
            <div class="text-secondary-text">{{ price_output_unit_name }}</div>
          </div>
          <div class="cluster full-width" data-gap="lg">
            <div class="km-field text-secondary-text pl-sm mb-sm">
              Price for reasoning output {{ price_output_unit_name }}
              <km-input v-model="price_reasoning_output" prefix="$" height="32px" class="pricing__amount-input" />
            </div>
            <div class="text-secondary-text">per</div>
            <km-input v-model="price_reasoning_output_unit_count" height="32px" class="pricing__count-input" />
            <div class="text-secondary-text">{{ price_output_unit_name }}</div>
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
export default {
  props: [],
  emits: [],

  setup() {
    const queries = useEntityQueries()
    const { draft, updateField } = useEntityDetail('model')
    const { data: providerData } = queries.provider.useList()
    const providerItems = computed(() => providerData.value?.items ?? [])

    return {
      draft,
      updateField,
      providerItems,
      priceUnitOptions: ref([
        { label: 'Tokens', value: 'tokens' },
        { label: 'Characters', value: 'characters' },
        { label: 'Queries', value: 'queries' },
      ]),
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
        return this.draft?.model || ''
      },
      set(value) {
        this.updateField('model', value)
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

<style scoped>
.pricing__label {
  min-inline-size: 140px;
}

.pricing__amount-input {
  max-inline-size: 200px;
}

.pricing__count-input {
  max-inline-size: 150px;
}
</style>
