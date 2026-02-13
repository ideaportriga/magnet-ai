<template lang="pug">
.col-auto.q-py-auto
  .km-heading-4 {{ activeRagName }}
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
  km-btn(label='Save', icon='far fa-save', color='primary', bg='background', iconSize='16px', @click='save')
.col-auto.text-white.q-mr-md
  q-btn.q-px-xs(data-test='show-more-btn', flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showNewDialog = true', dense)
        q-item-section
          .km-heading-3 Clone
      q-item(data-test='delete-btn', clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete

configuration-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false', copy)
q-inner-loading(:showing='loading')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete RAG Tool',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteRag',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the RAG Tool
  .row.text-center.justify-center This action will permanently delete the RAG Tool and disable it in all tools that are using it.
</template>

<script>
import { useChroma } from '@shared'
import { ref } from 'vue'

export default {
  props: ['activeRagTool'],
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('rag_tools')

    return {
      items,
      update,
      create,
      selectedRow,
      useCollection,
      loading: ref(false),
      showNewDialog: ref(false),
      showDeleteDialog: ref(false),
    }
  },

  computed: {
    created_at() {
      if (!this.activeRagDB?.created_at) return ''
      return `${this.formatDate(this.activeRagDB.created_at)}`
    },
    updated_at() {
      if (!this.activeRagDB?.updated_at) return ''
      return `${this.formatDate(this.activeRagDB.updated_at)}`
    },
    created_by() {
      if (!this.activeRagDB?.created_by) return 'Unknown'
      return `${this.activeRagDB?.created_by}`
    },
    updated_by() {
      if (!this.activeRagDB?.updated_by) return 'Unknown'
      return `${this.activeRagDB?.updated_by}`
    },
    currentRag() {
      return this.$store.getters.rag
    },
    route() {
      return this.$route
    },
    activeRagId() {
      return this.$route.params.id
    },
    activeRagDB() {
      return this.items.find((item) => item.id == this.activeRagId)
    },
    activeRagName: {
      get() {
        return this.activeRagDB?.name
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
    deleteRag() {
      this.loadingDelelete = true
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'RAG Tool has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/rag-tools')
    },
    async openDetails(row) {
      await this.$router.push(`/rag-tools/${row.id}`)
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
    async save() {
      this.loading = true
      if (this.currentRag?.created_at) {
        await this.update({ id: this.currentRag.id, data: JSON.stringify(this.currentRag) })
      } else {
        await this.create(JSON.stringify(this.currentRag))
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
