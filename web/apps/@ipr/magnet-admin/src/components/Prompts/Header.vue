<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRowName }}
.col
.col-auto.q-mr-sm
  km-btn(label='Record info', icon='info', iconSize='16px') 
  q-tooltip.bg-white.block-shadow
    .q-pa-sm
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created:
        .text-secondary-text.km-description {{ created_at }}
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Modified:
        .text-secondary-text.km-description {{ updated_at }}
      .q-mb-sm
        .text-secondary-text.km-button-xs-text Created by:
        .text-secondary-text.km-description {{ created_by }}
      div
        .text-secondary-text.km-button-xs-text Modified by:
        .text-secondary-text.km-description {{ updated_by }}
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  km-btn(label='Save', icon='far fa-save', iconSize='16px', color='primary', bg='background', @click='save', :loading='loading', :disable='loading')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px', data-test='show-more-btn')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(clickable, @click='showDeleteDialog = true', dense, data-test='delete-btn')
        q-item-section
          .km-heading-3 Delete

prompts-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Prompt Template',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteRecord',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Prompt Template
  .row.text-center.justify-center This action will permanently delete the Prompt Template and disable it in all tools that are using it.
q-inner-loading(:showing='loading')
</template>

<script>
import { useChroma } from '@shared'
import { validSystemName } from '@shared/utils/validationRules'
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
      showDeleteDialog: ref(false),
    }
  },
  computed: {
    created_at() {
      if (!this.activeRowDB.created_at) return ''
      return `${this.formatDate(this.activeRowDB?.created_at)}`
    },
    updated_at() {
      if (!this.activeRowDB) return ''
      return `${this.formatDate(this.activeRowDB?.updated_at)}`
    },
    created_by() {
      if (!this.activeRowDB?.created_by) return 'Unknown'
      return `${this.activeRowDB?.created_by}`
    },
    updated_by() {
      if (!this.activeRowDB?.updated_by) return 'Unknown'
      return `${this.activeRowDB?.updated_by}`
    },
    currentRow() {
      return this.$store.getters.promptTemplate
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

  methods: {
    deleteRecord() {
      this.loadingDelelete = true
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Prompt Template has been deleted',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/prompt-templates')
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
      // Validate system_name before saving
      const systemNameValidation = validSystemName()(this.currentRow?.system_name)
      if (systemNameValidation !== true) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: systemNameValidation,
          timeout: 3000,
        })
        return
      }

      this.loading = true
      try {
        if (this.currentRow?.created_at) {
          const obj = { ...this.currentRow }
          await this.update({ id: obj.id, data: JSON.stringify(obj) })
        } else {
          await this.create(JSON.stringify(this.currentRow))
        }
        this.$store.commit('setInitPromptTemplate')
        this.$q.notify({
          position: 'top',
          color: 'positive',
          message: 'Saved successfully',
          timeout: 2000,
        })
      } catch (error) {
        this.$q.notify({
          position: 'top',
          color: 'negative',
          message: error.message || 'Failed to save',
          timeout: 3000,
        })
      } finally {
        this.loading = false
      }
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
