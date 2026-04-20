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
            q-chip.q-mr-sm(:label='m.common_active()', color='primary-light', text-color='primary', flat, size='sm')

            //- q-item-label.km-label {{opt}} 
  .col.q-mx-sm
    km-input-flat.km-description.full-width(:placeholder='m.common_description()', :modelValue='variant_description', @change='variant_description = $event')
  .col-auto.q-mr-sm
    km-btn.width-100(
      v-if='!isActive',
      :label='m.common_activate()',
      icon='far fa-circle-check',
      iconColor='icon',
      hoverColor='primary',
      labelClass='km-title',
      flat,
      iconSize='16px',
      hoverBg='primary-bg',
      @click='doActivateVariant'
    )
    q-chip.q-mr-sm(v-if='isActive', :label='m.common_active()', color='primary-light', text-color='primary')
  q-separator(vertical, color='white')
  .col-auto.text-white.q-mx-md
    km-btn(
      :label='m.common_copyToNew()',
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
import { m } from '@/paraglide/messages'
import { useCatalogOptions } from '@/queries/useCatalogOptions'
import { useAgentEntityDetail } from '@/composables/useAgentEntityDetail'
import { notify } from '@shared/utils/notify'

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
      m,
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
      notify.success(m.common_variantActivated())
    },
    addVariant() {
      this.createVariant()
      notify.success(m.common_variantAdded())
    },
    doDeleteVariant() {
      this.confirm(m.common_deleteVariantConfirm(), () => this.deleteVariant())
    },

    confirm(message, callback) {
      notify.confirm({
        message,
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          callback()
          notify.success(m.common_variantDeleted())
        },
      })
    },

    deleteAgentDetail() {
      notify.confirm({
        message: m.agents_deleteAgentConfirm(),
        confirmLabel: m.common_delete(),
        cancelLabel: m.common_cancel(),
        onConfirm: () => {
          this.loadingDelelete = true
          this.removeEntity(this.$route.params.id)
          this.$emit('update:closeDrawer', null)
          notify.success(m.agents_promptDeleted())
          this.navigate('/prompt-templates')
        },
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
