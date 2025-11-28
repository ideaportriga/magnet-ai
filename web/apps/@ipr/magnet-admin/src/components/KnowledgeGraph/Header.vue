<template>
  <div class="col-auto q-py-auto">
    <div class="km-heading-4">{{ graphName }}</div>
  </div>
  <div class="col" />
  <div class="col-auto q-mr-sm">
    <km-btn label="Record info" icon="info" icon-size="16px" />
    <q-tooltip class="bg-white block-shadow">
      <div class="q-pa-sm">
        <div class="q-mb-sm">
          <div class="text-secondary-text km-button-xs-text">Created:</div>
          <div class="text-secondary-text km-description">{{ createdAt }}</div>
        </div>
        <div>
          <div class="text-secondary-text km-button-xs-text">Last Synced:</div>
          <div class="text-secondary-text km-description">{{ modifiedAt }}</div>
        </div>
      </div>
    </q-tooltip>
  </div>
  <q-separator vertical color="white" />
  <div class="col-auto text-white q-ml-md q-mr-md">
    <q-btn class="q-px-xs" flat :icon="'fas fa-ellipsis-v'" size="13px">
      <q-menu anchor="bottom right" self="top right">
        <q-item clickable dense @click="showDeleteDialog = true">
          <q-item-section>
            <div class="km-heading-3">Delete</div>
          </q-item-section>
        </q-item>
      </q-menu>
    </q-btn>
  </div>
  <km-popup-confirm
    :visible="showDeleteDialog"
    confirm-button-label="Delete Knowledge Graph"
    cancel-button-label="Cancel"
    notification-icon="fas fa-triangle-exclamation"
    @confirm="deleteGraph"
    @cancel="showDeleteDialog = false"
  >
    <div class="row item-center justify-center km-heading-7">You are about to delete this Knowledge Graph</div>
    <div class="row text-center justify-center">
      This action will permanently delete the Knowledge Graph and disable it in all tools that are using it.
    </div>
  </km-popup-confirm>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'

const router = useRouter()
const route = useRoute()
const store = useStore()
const $q = useQuasar()
const graphName = ref('')
const createdAt = ref('')
const modifiedAt = ref('')
const showDeleteDialog = ref(false)
const deleting = ref(false)

const graphId = computed(() => route.params.id as string)

const load = async () => {
  if (!graphId.value) return
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${graphId.value}`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      graphName.value = data?.name || ''
      createdAt.value = data?.created_at || ''
      modifiedAt.value = data?.updated_at || ''
    }
  } catch (e) {
    // noop
  }
}

const deleteGraph = async () => {
  deleting.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs//${graphId.value}`,
      method: 'DELETE',
      credentials: 'include',
    })

    if (response.ok) {
      $q.notify({
        position: 'top',
        message: 'Knowledge graph deleted successfully',
        color: 'positive',
        textColor: 'black',
        timeout: 1000,
      })
      router.push('/knowledge-graph')
    } else {
      $q.notify({
        position: 'top',
        message: 'Failed to delete knowledge graph',
        color: 'error-text',
        timeout: 1000,
      })
    }
  } catch (error) {
    console.error('Error deleting graph:', error)
    $q.notify({
      position: 'top',
      message: 'Error deleting knowledge graph',
      color: 'error-text',
      timeout: 1000,
    })
  } finally {
    deleting.value = false
  }
}

onMounted(load)
</script>
