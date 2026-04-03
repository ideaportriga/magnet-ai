<template lang="pug">
q-separator.q-my-sm
.row.items-center
  .col-auto.q-py-auto
    km-select.bg-white(:options='variantOptions', v-model='selected_variant', bg-color='background', height='30px', hasDropdownSearch)
      template(#option='{ itemProps, opt, selected, toggleOption }')
        q-item.ba-border(v-bind='itemProps', dense)
          q-item-section
            q-item-label.km-label {{ opt.label }}
          q-item-section(v-if='opt?.active_variant', avatar)
            q-chip.q-mr-sm(label='Active', color='primary-light', text-color='primary', flat, size='sm')

            //- q-item-label.km-label {{opt}} 
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
      @click='doActivateVariant'
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
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='doDeleteVariant', :disable='variantOptions?.length === 1')

  prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
  km-inner-loading(:showing='loading')
</template>

<script>
import { ref, computed } from 'vue'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const { options: items } = useCatalogOptions('agents')
    const { draft, isDirty, updateField, updateVariantField,
            selectedVariant, activeVariant, variants, setSelectedVariant,
            createVariant, deleteVariant, activateVariant,
            save, revert } = useAgentEntityDetail()

    return {
      draft,
      isDirty,
      updateField,
      updateVariantField,
      selectedVariant,
      activeVariant,
      variants,
      setSelectedVariant,
      createVariant: createVariant,
      deleteVariant: deleteVariant,
      activateVariant: activateVariant,
      save,
      revert,
      items,
      loading: ref(false),
      showNewDialog: ref(false),
    }
  },
  computed: {
    isActive() {
      return this.selectedVariant == this.draft?.active_variant
    },
    selected_variant: {
      get() {
        return this.getVariantLabel(this.selectedVariant)
      },
      set(value) {
        this.setSelectedVariant(value.value)
      },
    },
    variantOptions() {
      return this.draft?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
        value: el.variant,
        active_variant: el.variant == this.draft?.active_variant,
      }))
    },
    variant_description: {
      get() {
        return this.activeVariant?.value?.description
      },
      set(value) {
        this.updateVariantField('description', value)
      },
    },
    created_at() {
      if (!this.activeRowDB?.created_at) return ''
      return `${this.formatDate(this.activeRowDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRowDB?.updated_at) return ''
      return `${this.formatDate(this.activeRowDB.updated_at)}`
    },
    currentRow() {
      return this.draft
    },
    route() {
      return this.$route
    },
    activeRowId() {
      return this.$route.params.id
    },
    activeRowDB() {
      return this.items.find((item) => item.id == this.activeRowId)
    },

    activeRowName: {
      get() {
        return this.activeRowDB?.name
      },
      set(val) {
        this.openDetails(val.value)
      },
    },
    options() {
      return this.items.map((item) => ({ label: item.name, value: item }))
    },
  },
  watch: {},
  created() {},

  methods: {
    getVariantLabel(variant) {
      const match = variant?.match(/variant_(\d+)/)
      return `Variant ${match?.[1]}`
    },
    doActivateVariant() {
      this.activateVariant()
      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'Variant has been activated.',
        timeout: 1000,
      })
    },
    addVariant() {
      this.createVariant()
      this.$q.notify({
        color: 'green-9', textColor: 'white',
        icon: 'check_circle',
        group: 'success',
        message: 'New variant has been added.',
        timeout: 1000,
      })
    },
    doDeleteVariant() {
      this.confirm('Are you sure you want to delete this variant?', () => this.deleteVariant())
    },

    confirm(message, callback) {
      // notify with confirmation
      this.$q.notify({
        message,
        color: 'red-9', textColor: 'white',
        icon: 'error',
        group: 'error',
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
              // notify with success
              callback()
              this.$q.notify({
                color: 'green-9', textColor: 'white',
                icon: 'check_circle',
                group: 'success',
                message: 'Variant has been deleted.',
                timeout: 1000,
              })
            },
          },
        ],
      })
    },

    deleteAgentDetail() {
      this.$q.notify({
        message: `Are you sure you want to delete this agent?`,
        color: 'red-9', textColor: 'white',
        icon: 'error',
        group: 'error',
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
              this.loadingDelelete = true
              this.removeEntity(this.$route.params.id)
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                color: 'green-9', textColor: 'white',
                icon: 'check_circle',
                group: 'success',
                message: 'Prompt has been deleted.',
                timeout: 1000,
              })
              this.navigate('/prompt-templates')
            },
          },
        ],
      })
    },
    async openDetails(row) {
      await this.$router.push(`/prompt-templates/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async doSave() {
      this.loading = true
      await this.save()
      this.loading = false
    },
    formatDate(date) {
      const dateObject = new Date(date)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString()
      return `${localeDateString} ${localeTimeString}`
    },
  },
}
</script>
