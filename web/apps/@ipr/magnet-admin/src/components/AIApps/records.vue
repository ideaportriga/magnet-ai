<template lang="pug">
.col
  .row.justify-center.fit.q-gap-16.items-center(v-if='tabs.length === 0')
    .col-auto
      km-empty-state(@click='showNewDialog = true')

  div(v-else)
    .row.q-mb-12
      .col-auto.center-flex-y
      q-space
      .col-auto.center-flex-y
        km-btn.q-mr-12(label='New', @click='showNewDialog = true')

    VueDraggable.row.q-pb-12(v-model='tabs', group='nested', draggable='.drag-elem', @start='handleDragStart', @end='handleDragEnd')
      .drag-elem(v-for='item in tabs', :key='item.id')
        ai-apps-record(
          :row='item',
          :hovered='hovered',
          :isMoving='isMoving',
          :openTabDetails='openTabDetails',
          :setInactive='() => toggleItemInactive(item)',
          :removeRecord='() => handleRemoveRecord(item.system_name)'
        )

        VueDraggable.inner-list(
          v-if='item.tab_type === "Group"',
          :modelValue='item.children ?? []',
          @update:modelValue='item.children = $event',
          group='nested',
          draggable='.drag-elem',
          style='margin-left: 36px'
        )
          .drag-elem(v-for='innerItem in item.children', :key='innerItem.id')
            ai-apps-record(
              :row='innerItem',
              :hovered='hovered',
              :isMoving='isMoving',
              :openTabDetails='(row) => openTabDetails(row, item)',
              :setInactive='() => toggleInnerItemInactive(innerItem)',
              :removeRecord='() => handleRemoveInnerRecord(item.system_name, innerItem.system_name)'
            )

          .q-pa-xs.col-xs-12.empty-placeholder(v-if='!item.children?.length && isMoving && draggedRow.tab_type !== "Group"')
            q-card.card-hover.flex.justify-center.items-center(bordered, flat, style='min-width: 400px; min-height: 63px')
              div +

  ai-app-tabs-create-new(v-if='showNewDialog', :showNewDialog='showNewDialog', @cancel='showNewDialog = false')

  km-popup-confirm(
    :visible='showDeleteDialog',
    confirmButtonLabel='Delete',
    cancelButtonLabel='Cancel',
    notificationIcon='fas fa-triangle-exclamation',
    @confirm='deleteTab(clickedRow)',
    @cancel='showDeleteDialog = false'
  )
    .row.item-center.justify-center.km-heading-7 You are about to delete an AI Tab
    .row.text-center.justify-center End users won't see any changes until you save the AI App.
</template>

<script setup>
import { ref, computed, watch, onMounted, onActivated } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { VueDraggable } from 'vue-draggable-plus'
import { useAiAppDetailStore } from '@/stores/entityDetailStores'
import { useSearchStore } from '@/stores/searchStore'

// Composables
const route = useRoute()
const router = useRouter()
const aiAppStore = useAiAppDetailStore()
const searchStore = useSearchStore()
const selected = ref([])
const queries = useEntityQueries()
const routeId = ref(route.params?.id)
onActivated(() => { routeId.value = route.params?.id })
const { data: selectedRow } = queries.ai_apps.useDetail(routeId)
const { data: aiAppsListData } = queries.ai_apps.useList()
const aiAppsItems = computed(() => aiAppsListData.value?.items ?? [])

// Reactive state
const activeAIApp = ref({})
const prompt = ref(null)
const openTest = ref(true)
const openCreateDialog = ref(true)
const showInfo = ref(false)
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const searchString = ref('')
const hovered = ref({})
const isMoving = ref(false)
const clickedRow = ref({})
const draggedRow = ref({})

// Computed properties
const name = computed({
  get: () => aiAppStore.entity?.name || '',
  set: (value) => aiAppStore.updateProperty({ key: 'name', value }),
})

const description = computed({
  get: () => aiAppStore.entity?.description || '',
  set: (value) => aiAppStore.updateProperty({ key: 'description', value }),
})

const system_name = computed({
  get: () => aiAppStore.entity?.system_name || '',
  set: (value) => aiAppStore.updateProperty({ key: 'system_name', value }),
})

const tabs = computed({
  get: () => aiAppStore.entity?.tabs || [],
  set: (value) => {
    aiAppStore.updateProperty({ key: 'tabs', value })
  },
})

const searchedTabs = computed({
  get: () => tabs.value.filter((tab) => tab.name.toLowerCase().includes(searchString.value.toLowerCase())),
  set: (value) => {
    tabs.value = value
  },
})

const activeAIAppId = computed(() => route.params?.id)

const activeAIAppName = computed(() => aiAppsItems.value?.find((item) => item?.id == activeAIAppId.value)?.name)

const options = computed(() => aiAppsItems.value?.map((item) => item?.name))

const loading = computed(() => !aiAppStore.entity?.id)

// Methods
const navigate = (path = '') => {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

const openTabDetails = (row, parent = null) => {
  // console.log(parent, row)
  if (parent) {
    const link_encoded_row = encodeURIComponent(row.system_name)
    navigate(`${route.path}/items/${parent.system_name}?child=${link_encoded_row}`)
  } else {
    navigate(`${route.path}/items/${row.system_name}`)
  }
}

const deleteTab = (payload) => {
  const currentTabs = aiAppStore.entity?.tabs || []
  let newTabs
  if (typeof payload === 'string') {
    newTabs = currentTabs.filter((el) => el.system_name !== payload)
  } else {
    const parentName = payload[0]
    const systemName = payload[1]
    newTabs = currentTabs.map((el) => {
      if (el.system_name === parentName) {
        return { ...el, children: el.children.filter((c) => c.system_name !== systemName) }
      }
      return el
    })
  }
  aiAppStore.updateProperty({ key: 'tabs', value: newTabs })
  showDeleteDialog.value = false
}

// Event handlers
const handleDragStart = (row) => {
  isMoving.value = true
  hovered.value = {}
  draggedRow.value = row.data
}

const handleDragEnd = () => {
  isMoving.value = false
  draggedRow.value = null
}

const toggleItemInactive = (item) => {
  item.inactive = !item.inactive
}

const toggleInnerItemInactive = (innerItem) => {
  innerItem.inactive = !innerItem.inactive
}

const handleRemoveRecord = (systemName) => {
  clickedRow.value = systemName
  showDeleteDialog.value = true
}

const handleRemoveInnerRecord = (parentSystemName, innerSystemName) => {
  clickedRow.value = [parentSystemName, innerSystemName]
  showDeleteDialog.value = true
}

// Watchers
watch(selectedRow, (newVal, oldVal) => {
  if (newVal?.id !== oldVal?.id) {
    aiAppStore.setEntity(newVal)
    searchStore.clearAnswers()
  }
})

// Lifecycle
onMounted(() => {
  if (activeAIAppId.value != aiAppStore.entity?.id) {
    aiAppStore.setEntity(selectedRow.value)
    searchStore.clearAnswers()
  }
})
</script>

<style lang="stylus">
// Drag and drop elements
.drag-elem
  width 100%

.inner-list
  // Hide empty placeholder when ghost element is present
  &:has(.sortable-ghost)
    .empty-placeholder
      display none

// Empty placeholder styling
.empty-placeholder
  .card-hover
    &:hover
      background var(--q-background)
      cursor pointer
      border-color var(--q-primary)

// Utility classes (commented out for future use)
.gradient
  background linear-gradient(121.5deg, var(--q-primary) 9.69%, var(--q-error) 101.29%)
  -webkit-background-clip text
  -webkit-text-fill-color transparent

// Animations (commented out for future use)
@keyframes wobble
  0%
    transform rotate(-5deg)
  50%
    transform rotate(5deg)
  100%
    transform rotate(-5deg)

.wobble
  animation wobble 2s infinite
</style>
