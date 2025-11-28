<template lang="pug">
template(v-if='variants')
  .km-field.text-left.cursor-pointer(v-for='variant in variants') 
    div {{ variant?.name }}
    q-tooltip(:offset='[0, 10]')
      .row.items-center
        .col-auto.q-mr-sm
          .km-field Variant:
        .col-auto
          .km-heading-1 {{ variant?.name }}
      .row.items-center.q-mt-xs(v-if='variant?.model')
        .col-auto.q-mr-sm
          .km-field Model:
        .col-auto
          .km-heading-1 {{ variant?.model }}
      .row.items-center.q-mt-xs(v-if='variant?.description')
        .col-auto.q-mr-sm
          .km-field Description:
        .col-auto
          .km-heading-1 {{ variant?.description }}
</template>
<script>
import { defineComponent } from 'vue'
import { typeOptions } from '@/config/evaluation_sets/evaluation_sets'

export default defineComponent({
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
      const objModel = this.$store.getters['chroma/model'].items?.find((model) => model.system_name == system_name)
      return objModel?.display_name || ''
    },
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
  },
})
</script>
