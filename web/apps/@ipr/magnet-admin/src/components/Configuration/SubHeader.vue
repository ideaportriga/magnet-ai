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
import { useChroma } from '@shared'
import { ref } from 'vue'

export default {
  props: ['activeRow'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('promptTemplates')

    return {
      items,
      update,
      create,
      selectedRow,
      loading: ref(false),
      useCollection,
      showNewDialog: ref(false),
    }
  },
  computed: {
    isActive() {
      return this.$store.getters.selectedRagVariant == this.$store.getters.rag?.active_variant
    },
    selected_variant: {
      get() {
        return this.getVariantLabel(this.$store.getters.selectedRagVariant)
      },
      set(value) {
        this.$store.commit('setSelectedRagVariant', value.value)
      },
    },
    variants() {
      return this.$store.getters.rag?.variants?.map((el) => ({
        label: this.getVariantLabel(el.variant),
        value: el.variant,
        active_variant: el.variant == this.$store.getters.rag?.active_variant,
      }))
    },
    variant_description: {
      get() {
        return this.$store.getters.ragVariant?.description
      },
      set(value) {
        this.$store.commit('updateNestedRagProperty', { path: 'description', value })
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
      return this.$store.getters.rag
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
    confirm(message, callback) {
      // notify with confirmation
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
              // notify with success
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
      this.$store.commit('activateRagVariant')
      this.$q.notify({
        position: 'top',
        message: 'Variant has been activated.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    addVariant() {
      this.$store.commit('createRagVariant')
      this.$q.notify({
        position: 'top',
        message: 'New variant has been added.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
    },
    deleteVariant() {
      this.confirm('Are you sure you want to delete this variant?', () => this.$store.commit('deleteRagVariant'))
    },

    deleteRag() {
      this.$q.notify({
        message: `Are you sure you want to delete ${this.selectedRow?.name}?`,
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
              this.loadingDelelete = true
              this.useCollection.delete({ id: this.selectedRow?.id })
              this.$emit('update:closeDrawer', null)
              this.$q.notify({
                position: 'top',
                message: 'Prompt has been deleted.',
                color: 'positive',
                textColor: 'black',
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
    async save() {
      this.loading = true
      if (this.currentRow?.created_at) {
        const obj = { ...this.currentRow }
        delete obj._metadata
        console.log(obj)
        await this.update({ id: obj.id, data: JSON.stringify(obj) })
      } else {
        await this.create(JSON.stringify(this.currentRow))
      }
      this.$store.commit('setInitRag')
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
