<template lang="pug">
q-separator.q-my-sm
.row.items-center
  .col-auto.q-py-auto
    km-select-flat.bg-white(:options='variants', v-model='selected_variant', bg-color='background', height='30px', hasDropdownSearch)
      template(#option='{ itemProps, select, option }')
        q-item.bb-border(clickable, v-bind='itemProps', dense, @click='select(option)')
          q-item-section
            q-item-label.km-label {{ option.label }}
          q-item-section(v-if='option?.active_variant', avatar)
            q-chip.q-mr-sm(:label='m.common_activate()', color='primary-light', text-color='primary', flat, size='sm')
    //- km-select(:options="variants" v-model="selected_variant" bg-color="background", height="30px", hasDropdownSearch).bg-white
    //-   template(#option="{ itemProps, opt, selected, toggleOption }")
    //-     q-item.ba-border(v-bind='itemProps' dense)
    //-       q-item-section
    //-         q-item-label.km-label {{opt.label}} 
    //-       q-item-section(v-if="opt?.active_variant" avatar)
    //-         q-chip.q-mr-sm(
    //-         label="Active"
    //-         color="primary-light"
    //-         text-color="primary"
    //-         flat
    //-         size="sm"
    //-         )
      //- q-item-label.km-label {{opt}} 
  .col.q-mx-sm
    km-input-flat.km-description.full-width(placeholder='Description', :modelValue='variant_description', @change='variant_description = $event')
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
      @click='activateVariantAction'
    )
    q-chip.q-mr-sm(v-if='isActive', :label='m.common_activate()', color='primary-light', text-color='primary')

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
    km-btn.q-mx-xs(flat, :icon='"far fa-trash-can"', iconSize='16px', size='13px', @click='deleteVariantAction', :disable='variants?.length === 1')

  prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
  km-inner-loading(:showing='loading')
</template>

<script>
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import { useVariantEntityDetail } from '@/composables/useVariantEntityDetail'
import { ref, computed } from 'vue'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const queries = useEntityQueries()
    const { draft, isDirty, selectedVariant, activeVariant, variants: variantsRaw,
            updateVariantField, setSelectedVariant, createVariant, deleteVariant,
            activateVariant, save, buildPayload } = useVariantEntityDetail('promptTemplates')
    const { data: listData } = queries.promptTemplates.useList()
    const { mutateAsync: updateEntity } = queries.promptTemplates.useUpdate()
    const { mutateAsync: createEntity } = queries.promptTemplates.useCreate()
    const { mutateAsync: removeEntity } = queries.promptTemplates.useRemove()
    const items = computed(() => listData.value?.items ?? [])

    return {
      draft,
      isDirty,
      selectedVariant,
      activeVariant,
      variantsRaw,
      updateVariantField,
      setSelectedVariant,
      createVariant: createVariant,
      deleteVariant: deleteVariant,
      activateVariant: activateVariant,
      composableSave: save,
      buildPayload,
      items,
      updateEntity,
      createEntity,
      removeEntity,
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
    variants() {
      return this.draft?.variants?.map((el) => ({
        label: el.display_name || this.getVariantLabel(el.variant),
        value: el.variant,
        active_variant: el.variant == this.draft?.active_variant,
      }))
    },
    variant_description: {
      get() {
        return this.activeVariant?.description
      },
      set(value) {
        this.updateVariantField('description', value)
      },
    },
    created_at() {
      if (!this.activeRowDB.created_at) return ''
      return `${this.formatDate(this.activeRowDB.created_at)}`
    },
    modified_at() {
      if (!this.activeRowDB.updated_at) return ''
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
      const v = this.draft?.variants?.find((el) => el.variant === variant)
      if (v?.display_name) return v.display_name

      const match = variant?.match(/variant_(\d+)/)
      if (!match) return variant
      return `Variant ${match?.[1]}`
    },
    activateVariantAction() {
      this.activateVariant()
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Variant has been activated.', timeout: 1000 })
    },
    addVariant() {
      this.createVariant()
      this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'New variant has been added.', timeout: 1000 })
    },
    deleteVariantAction() {
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
              this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Variant has been deleted.', timeout: 1000 })
            },
          },
        ],
      })
    },

    deletePromptTemplate() {
      this.$q.notify({
        message: `Are you sure you want to delete this prompt template?`,
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
              this.$q.notify({ color: 'green-9', textColor: 'white', icon: 'check_circle', group: 'success', message: 'Prompt has been deleted.', timeout: 1000 })
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
    async save() {
      this.loading = true
      await this.composableSave()
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
