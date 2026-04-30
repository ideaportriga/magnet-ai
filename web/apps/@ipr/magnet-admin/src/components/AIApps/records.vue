<template>
  <div class="flex-1">
    <div v-if="tabs.length === 0" class="cluster fit" data-justify="center" data-gap="lg">
      <div class="flex-none">
        <km-empty-state @click="showNewDialog = true" />
      </div>
    </div>
    <div v-else>
      <div class="cluster mb-md">
        <div class="flex-none center-flex-y" />
        <div class="km-space" />
        <div class="flex-none center-flex-y">
          <km-btn class="mr-md" :label="m.common_new()" @click="showNewDialog = true" />
        </div>
      </div>
      <VueDraggable v-model="tabs" class="cluster pb-md" group="nested" draggable=".drag-elem" @start="handleDragStart" @end="handleDragEnd">
        <div v-for="item in tabs" :key="item.id" class="drag-elem">
          <ai-apps-record :row="item" :hovered="hovered" :is-moving="isMoving" :open-tab-details="openTabDetails" :set-inactive="() =&gt; toggleItemInactive(item)" :remove-record="() =&gt; handleRemoveRecord(item.system_name)" @hover="(name, val) =&gt; (hovered[name] = val)" />
          <VueDraggable v-if="item.tab_type === &quot;Group&quot;" class="inner-list" :model-value="item.children ?? []" group="nested" draggable=".drag-elem" style="margin-inline-start: 36px" @update:model-value="item.children = $event">
            <div v-for="innerItem in item.children" :key="innerItem.id" class="drag-elem">
              <ai-apps-record :row="innerItem" :hovered="hovered" :is-moving="isMoving" :open-tab-details="(row) =&gt; openTabDetails(row, item)" :set-inactive="() =&gt; toggleInnerItemInactive(innerItem)" :remove-record="() =&gt; handleRemoveInnerRecord(item.system_name, innerItem.system_name)" @hover="(name, val) =&gt; (hovered[name] = val)" />
            </div>
            <div v-if="!item.children?.length &amp;&amp; isMoving &amp;&amp; draggedRow.tab_type !== &quot;Group&quot;" class="p-xs basis-12 empty-placeholder">
              <km-card class="card-hover flex justify-center items-center" bordered flat style="min-inline-size: 400px; min-block-size: 63px">
                <div>+</div>
              </km-card>
            </div>
          </VueDraggable>
        </div>
      </VueDraggable>
    </div>
    <ai-app-tabs-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
    <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteTab(clickedRow)" @cancel="showDeleteDialog = false">
      <div class="cluster km-heading-7" data-justify="center">{{ m.deleteConfirm_aboutToDelete({ entity: m.common_aiTabs() }) }}</div>
      <div class="cluster text-center" data-justify="center">{{ m.aiApps_deleteTabNotice() }}</div>
    </km-popup-confirm>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueDraggable } from 'vue-draggable-plus'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { useSearchStore } from '@/stores/searchStore'
import { m } from '@/paraglide/messages'

// Composables
const route = useRoute()
const router = useRouter()
const { draft, isLoading, updateField } = useEntityDetail('ai_apps')
const searchStore = useSearchStore()
const selected = ref([])

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
  get: () => draft.value?.name || '',
  set: (value) => updateField('name', value),
})

const description = computed({
  get: () => draft.value?.description || '',
  set: (value) => updateField('description', value),
})

const system_name = computed({
  get: () => draft.value?.system_name || '',
  set: (value) => updateField('system_name', value),
})

const tabs = computed({
  get: () => draft.value?.tabs || [],
  set: (value) => {
    updateField('tabs', value)
  },
})

const searchedTabs = computed({
  get: () => tabs.value.filter((tab) => tab.name.toLowerCase().includes(searchString.value.toLowerCase())),
  set: (value) => {
    tabs.value = value
  },
})

const activeAIAppId = computed(() => route.params?.id)

const loading = computed(() => isLoading.value || !draft.value?.id)

// Methods
const navigate = (path = '') => {
  if (route.path !== `/${path}`) {
    router.push(`${path}`)
  }
}

const openTabDetails = (row, parent = null) => {
  if (parent) {
    const link_encoded_row = encodeURIComponent(row.system_name)
    navigate(`${route.path}/items/${parent.system_name}?child=${link_encoded_row}`)
  } else {
    navigate(`${route.path}/items/${row.system_name}`)
  }
}

const deleteTab = (payload) => {
  const currentTabs = draft.value?.tabs || []
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
  updateField('tabs', newTabs)
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
</script>

<style>
.drag-elem {
  inline-size: 100%;
}
.inner-list:has(.sortable-ghost) .empty-placeholder {
  display: none;
}
.empty-placeholder .card-hover:hover {
  background: var(--ds-color-background);
  cursor: pointer;
  border-color: var(--ds-color-primary);
}
.gradient {
  background: linear-gradient(121.5deg, var(--ds-color-primary) 9.69%, var(--ds-color-error) 101.29%);
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.wobble {
  animation: ds-attention-wobble var(--ds-duration-attention) infinite;
}
</style>
