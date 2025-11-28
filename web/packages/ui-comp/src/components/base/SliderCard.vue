<template lang="pug">
div(@mouseover='hover = true', @mouseleave='hover = false') 
  .row.items-center
    .col
      .row
        .km-button-text.q-mr-sm {{ name }}
        template(v-if='infoTooltip')
          q-icon(name='o_info', size='20px', color='secondary')
            q-tooltip.bg-white.block-shadow.text-secondary-text.km-description(self='top middle', :offset='[-50, -50]') {{ infoTooltip }}
    .col-auto
      km-input-flat.km-input-label(
        :class='{ "bg-light": hover }',
        dense,
        :model-value='inputNumber',
        @change='inputNumber = $event',
        @input='inputNumber = $event',
        style='width: 50px !important; text-align: end'
      ) 
    .col-auto.q-ml-sm
      km-btn(icon='refresh', flat, simple, style='visibility: hidden; height: 1px !important')
  .row.center-flex-y
    .col.center-flex-y
      km-slider(:model-value='modelValue', @update:modelValue='$emit("update:modelValue", $event)', :min='min', :max='max', :step='step')
    .col-auto.q-ml-sm
      km-btn.text-text-gray(icon='refresh', flat, simple, @click='$emit("update:modelValue", this.defaultValue)', tooltip='Revert to default value')
  .row(style='margin-top: -8px')
    .col
      .km-description.text-secondary-text {{ minLabel }}
    .col-auto
      .km-description.text-secondary-text {{ maxLabel }}
    .col-auto.q-ml-sm
      km-btn(icon='refresh', flat, simple, style='visibility: hidden; height: 1px !important')
  .row.items-center.q-mt-8(v-if='description')
    .km-description.text-text-gray {{ description }}
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    modelValue: {},
    defaultValue: {
      type: Number,
      default: 0.5,
    },
    name: {
      type: String,
      default: 'Similarity score threshold',
    },
    description: {
      type: String,
      default: '',
    },
    minLabel: {
      type: String,
      default: 'Minimum',
    },
    maxLabel: {
      type: String,
      default: 'Maximum',
    },
    infoTooltip: {
      type: String,
      default: '',
    },
    min: {
      default: 0,
    },
    max: {
      default: 1,
    },
    step: {
      default: 0.01,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      hover: false,
    }
  },
  computed: {
    inputNumber: {
      get() {
        return this.modelValue
      },
      set(val) {
        // check number
        const numValue = parseFloat(val)

        if (!isNaN(numValue)) {
          if (numValue > this.max) this.$emit('update:modelValue', this.max)
          if (numValue < this.min) this.$emit('update:modelValue', this.min)
          if (numValue <= this.max && numValue >= this.min) this.$emit('update:modelValue', numValue)
        } else {
          this.$emit('update:modelValue', 0)
        }
      },
    },
  },
})
</script>
