<template lang="pug">
.col
q-separator(vertical, color='white')
.col-auto.text-white.q-mx-md
  q-btn.q-px-xs(flat, :icon='"fas fa-ellipsis-v"', size='13px')
    q-menu(anchor='bottom right', self='top right')
      q-item(clickable, @click='showDeleteDialog = true', dense)
        q-item-section
          .km-heading-3 Delete

km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete Trace',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteTrace',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 You are about to delete the Trace
  //.row.text-center.justify-center Deleting the Trace will also permanently delete its Topics with their interactions.
</template>

<script>
import { useChroma } from '@shared'

export default {
  emits: ['update:closeDrawer'],
  setup() {
    const { items, update, create, selectedRow, ...useCollection } = useChroma('observability_traces')

    return {
      items,
      update,
      create,
      selectedRow,
      useCollection,
    }
  },
  methods: {
    deleteTrace() {
      this.useCollection.delete({ id: this.selectedRow?.id })
      this.$emit('update:closeDrawer', null)
      this.$q.notify({
        position: 'top',
        message: 'Trace has been deleted.',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      this.navigate('/observability-traces')
    },
    navigate(path = '') {
      if (this.$route.path !== `/${path}`) {
        this.$router.push(`${path}`)
      }
    },
  },
}
</script>
