<template>
  <template v-if="variants">
    <div v-for="variant in variants" :key="variant" class="km-field text-left cursor-pointer"> 
      <div>{{ variant?.name }}</div>
      <km-tooltip :offset="[0, 10]">
        <div class="cluster">
          <div class="flex-none mr-sm">
            <div class="km-field">Variant:</div>
          </div>
          <div class="flex-none">
            <div class="km-heading-1">{{ variant?.name }}</div>
          </div>
        </div>
        <div v-if="variant?.model" class="cluster mt-xs">
          <div class="flex-none mr-sm">
            <div class="km-field">Model:</div>
          </div>
          <div class="flex-none">
            <div class="km-heading-1">{{ variant?.model }}</div>
          </div>
        </div>
        <div v-if="variant?.description" class="cluster mt-xs">
          <div class="flex-none mr-sm">
            <div class="km-field">Description:</div>
          </div>
          <div class="flex-none">
            <div class="km-heading-1">{{ variant?.description }}</div>
          </div>
        </div>
      </km-tooltip>
    </div>
  </template>
</template>
<script>
import { defineComponent } from 'vue'
import { typeOptions } from '@/config/evaluation_sets/evaluation_sets'
import { getCachedCatalog } from '@/queries/useCatalogOptions'

export default defineComponent({
  inheritAttrs: false,
  props: ['row'],

  setup() {
    return {
      typeOptions,
    }
  },

  computed: {
    variants() {
      let tools
      if (!this.row?.tools) {
        tools = [this.row?.tool]
      } else {
        tools = this.row?.tools
      }

      return tools
        ?.map((tool) => ({
          name: this.getVariantLabel(tool?.variant_name),
          description: tool?.variant_object?.description,
          model: this.getModelName(tool?.variant_object?.system_name_for_model),
        }))
        ?.sort((a, b) => a.name.localeCompare(b.name))
    },
  },
  methods: {
    getModelName(system_name) {
      const objModel = getCachedCatalog('model')?.find((model) => model.system_name == system_name)
      return objModel?.display_name || ''
    },
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
  },
})
</script>
