<template>
  <div class="stack p-md height-100 width-100" data-gap="md">
    <div class="stack" data-gap="xs">
      <h2 class="km-h2">Access log</h2>
      <div class="km-description text-grey">
        Audit trail of access-control changes in your tenant.
      </div>
    </div>

    <div class="cluster ba-border border-radius-8 bg-white p-md" data-gap="sm" data-wrap="yes" data-align="end">
      <div class="stack" data-gap="xs" style="min-inline-size: 180px">
        <label class="km-description">Action</label>
        <km-input
          v-model="actionFilter"
          placeholder="e.g. role.update"
          clearable
        />
      </div>
      <div class="stack" data-gap="xs" style="min-inline-size: 180px">
        <label class="km-description">Target type</label>
        <km-input
          v-model="targetTypeFilter"
          placeholder="e.g. role, user"
          clearable
        />
      </div>
      <div class="stack" data-gap="xs" style="min-inline-size: 220px">
        <label class="km-description">Actor ID</label>
        <km-input
          v-model="actorIdFilter"
          placeholder="UUID"
          clearable
        />
      </div>
      <km-btn label="Apply" @click="reload" />
      <km-btn flat label="Clear" @click="clearFilters" />
    </div>

    <div v-if="error" class="bg-error-bg p-md border-radius-6">
      <div class="text-error">{{ error }}</div>
    </div>

    <div v-if="loading" class="km-description text-grey p-md">Loading…</div>

    <div v-else class="stack ba-border border-radius-8 bg-white" data-gap="0">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="stack p-md bb-border"
        data-gap="xs"
      >
        <div class="cluster" data-gap="sm" data-align="center" data-wrap="yes">
          <km-chip tone="brand" size="sm" :label="entry.action" />
          <km-chip tone="muted" size="sm" :label="entry.target_type" />
          <span v-if="entry.target_id" class="km-description text-grey font-mono">
            {{ entry.target_id }}
          </span>
          <span class="km-description text-grey ml-auto">
            {{ formatDate(entry.created_at) }}
          </span>
        </div>
        <div v-if="entry.actor_id" class="km-description text-grey">
          actor: <span class="font-mono">{{ entry.actor_id }}</span>
        </div>
        <pre
          v-if="hasPayload(entry)"
          class="font-mono bg-grey-bg p-sm border-radius-6"
          style="white-space: pre-wrap; word-break: break-word; max-block-size: 200px; overflow: auto;"
        >{{ formatPayload(entry.payload) }}</pre>
      </div>
      <div v-if="!entries.length" class="km-description text-grey p-md">
        No log entries match the current filters.
      </div>
    </div>

    <div v-if="!loading" class="cluster" data-justify="between" data-align="center" data-wrap="no">
      <span class="km-description text-grey">
        Showing {{ entries.length }} entr{{ entries.length === 1 ? 'y' : 'ies' }}
        starting at offset {{ offset }}
      </span>
      <div class="cluster" data-gap="sm" data-wrap="no">
        <km-btn
          icon="chevron-left"
          flat
          label="Prev"
          :disabled="offset === 0"
          @click="prevPage"
        />
        <km-btn
          icon="chevron-right"
          flat
          label="Next"
          :disabled="entries.length < limit"
          @click="nextPage"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAccessLog, type AccessAuditEntry } from '@/api/adminAccess_ai-claude'

const entries = ref<AccessAuditEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const actionFilter = ref('')
const targetTypeFilter = ref('')
const actorIdFilter = ref('')
const limit = 50
const offset = ref(0)

async function load() {
  loading.value = true
  error.value = null
  try {
    entries.value = await listAccessLog({
      action: actionFilter.value.trim() || undefined,
      target_type: targetTypeFilter.value.trim() || undefined,
      actor_id: actorIdFilter.value.trim() || undefined,
      limit,
      offset: offset.value,
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function reload() {
  offset.value = 0
  load()
}

function clearFilters() {
  actionFilter.value = ''
  targetTypeFilter.value = ''
  actorIdFilter.value = ''
  reload()
}

function nextPage() {
  offset.value += limit
  load()
}

function prevPage() {
  offset.value = Math.max(0, offset.value - limit)
  load()
}

function hasPayload(entry: AccessAuditEntry): boolean {
  return entry.payload && Object.keys(entry.payload).length > 0
}

function formatPayload(payload: Record<string, unknown>): string {
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return String(payload)
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

onMounted(load)
</script>
