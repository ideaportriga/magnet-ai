<template lang="pug">
q-separator.q-my-sm
.row.items-center
  .col-auto.q-py-auto
    km-select-flat(:options='variants', v-model='selected_variant', bg-color='background', height='30px', hasDropdownSearch)
      template(#option='{ itemProps, select, option }')
        q-item.bb-border(clickable, v-bind='itemProps', dense, @click='select(option)')
          q-item-section
            q-item-label.km-label {{ option.label }}
          q-item-section(v-if='option?.active_variant', avatar)
            q-chip.q-mr-sm(label='Active', color='primary-light', text-color='primary', flat, size='sm')

  .col.q-mx-sm
    km-input-flat.km-description.full-width(placeholder='Description', :modelValue='variant_description', @change='variant_description = $event')
  .col-auto.q-mr-sm
    km-btn.width-100(
      v-if='!isActive',
      label='Activate',
      icon='far fa-circle-check',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='activateVariant'
    )
    q-chip.q-mr-sm(v-if='isActive', label='Active', color='primary-light', text-color='primary')

  q-separator(vertical, color='white')
  .col-auto.text-white.q-mx-md
    km-btn(
      label='Copy to new',
      icon='fas fa-plus',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='addVariant'
    )
  .col-auto.text-white.q-mr-md
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='deleteVariant', :disable='variants?.length === 1')

  prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
  q-inner-loading(:showing='loading')
</template>

<script>
import { ref } from 'vue'

export default {
  setup() {
    return {
      loading: ref(false),
      showNewDialog: ref(false),
    }
  },
  computed: {
    isActive() {
      return this.$store.getters.selectedRetrievalVariant == this.$store.getters.retrieval?.active_variant
    },
    selected_variant: {
      get() {
        return this.getVariantLabel(this.$store.getters.selectedRetrievalVariant)
      },
      set(value) {
        this.$store.commit('setSelectedRetrievalVariant', value.value)
      },
    },
    variants() {
      return this.$store.getters.retrieval?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
        value: el.variant,
        active_variant: el.variant == this.$store.getters.retrieval?.active_variant,
      }))
    },
    variant_description: {
      get() {
        return this.$store.getters.retrievalVariant?.description
      },
      set(value) {
        this.$store.commit('updateNestedRetrievalProperty', { path: 'description', value })
      },
    },
  },
  watch: {},
  created() {},

  methods: {
    confirm(message, callback) {
      this.$q.notify({
        message,
        color: 'error-text',
        position: 'top',
        timeout: 0,
        actions: [
          {
            label: 'Cancel',
            color: 'yellow',
            handler: () => {
              /* ... */
            },
          },
          {
            label: 'Delete',
            color: 'white',
            handler: () => {
              callback()
              this.$q.notify({
                position: 'top',
                message: 'Variant has been deleted.',
                color: 'positive',
                textColor: 'black',
                timeout: 1000,
              })
            },
          },
        ],
      })
    },
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    activateVariant() {
      this.$store.commit('activateRetrievalVariant')
      this.$q.notify({
        position: 'top',
        message: 'Variant has been activated.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    addVariant() {
      this.$store.commit('createRetrievalVariant')
      this.$q.notify({
        position: 'top',
        message: 'New variant has been added.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    deleteVariant() {
      this.confirm('Are you sure you want to delete this variant?', () => this.$store.commit('deleteRetrievalVariant'))
    },
  },
}
</script>
