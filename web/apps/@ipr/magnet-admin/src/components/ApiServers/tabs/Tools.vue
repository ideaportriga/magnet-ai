<template lang="pug">
.full-width.q-pb-lg(v-if='rows?.length')
  .row.q-mb-12.q-gap-12
    .col-auto.center-flex-y
      km-input(placeholder='Search', iconBefore='search', v-model='searchString', @input='debouncedUpdateSearch', clearable) 
    q-space
    .col-auto
      template(v-if='selected.length > 0')
        km-btn(@click='showDeleteDialog = true', icon='delete', flat, label='Delete')
    .col-auto
      km-btn(label='Add Tools', @click='showNewDialog = true')
  km-table-new.full-width.fit(
    :columns='columns',
    dense,
    :visibleColumns='visibleColumns',
    :rows='visibleRows',
    row-key='system_name',
    selection='multiple',
    @selectRow='handleRowClick',
    v-model:selected='selected'
  )
template(v-else)
  .column.justify-center.items-center.full-width.full-height
    .col.q-pa-xl.bg-light.border-radius-12
      .row.items-center.justify-center.q-mb-md
        q-icon(name='fa fa-arrow-right-arrow-left', size='48px', color='primary')
      .km-heading-7.text-black You have no API tools yet
      .km-description.text-black Use an API specification to create tools
      .row.items-center.justify-center.q-mt-lg
        km-btn(label='Add Tools', @click='showNewDialog = true')
api-servers-new-tools(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .km-title.q-pl-16.q-pb-8.q-pt-lg.text-text-grey.text-center Are you sure you want to delete the selected tools?
  .km-description.q-pl-16.q-pb-8.q-pt-lg.text-text-grey.text-center This action cannot be undone.
</template>

<script setup>
import { computed, ref } from 'vue'
import controls from '@/config/api_servers/tools'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { useQuasar } from 'quasar'
import { debounce } from 'lodash'

const router = useRouter()
const route = useRoute()
const store = useStore()
const q = useQuasar()
const showNewDialog = ref(false)
const searchString = ref('')
const selected = ref([])
const showDeleteDialog = ref(false)

const visibleColumns = computed(() => {
  return Object.keys(controls).filter((key) => controls[key])
})
const columns = computed(() => {
  return Object.values(controls)
})

const rows = computed(() => {
  return store.getters.api_server.tools
})
const debouncedUpdateSearch = debounce((value) => {
  searchString.value = value
}, 300)

const visibleRows = computed(() => {
  if (!searchString.value) return rows.value
  const fields = ['name', 'description']
  return rows.value.filter((item) => {
    return fields.some((field) => {
      return item[field].toLowerCase().includes(searchString.value.toLowerCase())
    })
  })
})

const handleRowClick = (row) => {
  router.push(`${route.path}/tools/${row.system_name}`)
}

const deleteSelected = () => {
  const removedTools = selected.value.map((tool) => tool.system_name)
  const remainingTools = rows.value.filter((tool) => !removedTools.includes(tool.system_name))
  store.dispatch('updateTools', remainingTools)
  selected.value = []
  showDeleteDialog.value = false
}
</script>
