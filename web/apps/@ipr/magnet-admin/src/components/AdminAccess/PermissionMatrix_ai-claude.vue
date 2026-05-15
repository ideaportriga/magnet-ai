<!--
  Reusable resource × action permission grid.

  Always renders the full catalog so the admin sees the complete picture.
  Codes that the current actor doesn't themselves hold are disabled (capability
  ceiling: you can't grant what you don't have). System roles render the same
  matrix in `readonly` mode without checkbox interaction.
-->
<template>
  <div class="stack" data-gap="md">
    <div v-if="readonly" class="km-description text-grey">
      System role — permissions are immutable.
    </div>
    <div
      v-for="group in groups"
      :key="group.resource"
      class="stack p-md ba-border border-radius-8"
      data-gap="sm"
    >
      <div class="cluster" data-align="center" data-justify="between" data-wrap="no">
        <div class="km-title">{{ formatResource(group.resource) }}</div>
        <km-chip
          size="sm"
          tone="muted"
          :label="`${countSelected(group)}/${group.entries.length}`"
        />
      </div>
      <div class="cluster" data-gap="sm" data-wrap="yes">
        <label
          v-for="entry in group.entries"
          :key="entry.code"
          class="cluster ba-border border-radius-6 px-sm py-xs"
          data-gap="xs"
          data-wrap="no"
          data-align="center"
          :class="entryDisabled(entry) ? 'opacity-60' : ''"
          :title="entryTooltip(entry)"
        >
          <input
            type="checkbox"
            :checked="selected.has(entry.code)"
            :disabled="readonly || entryDisabled(entry)"
            @change="toggle(entry.code)"
          >
          <span class="km-body">{{ entry.action }}</span>
        </label>
      </div>
    </div>
    <div v-if="!groups.length" class="km-description text-grey p-md">
      No permissions in catalog.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePermissions } from '@shared'
import type { PermissionEntry } from '@/api/adminAccess_ai-claude'

const props = defineProps<{
  catalog: PermissionEntry[]
  /** Currently selected permission codes. */
  modelValue: string[]
  /** Hide the controls and disable toggling (used for system roles). */
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', codes: string[]): void
}>()

const { can, isSuperuser } = usePermissions()

const selected = computed(() => new Set(props.modelValue))

interface Group {
  resource: string
  entries: PermissionEntry[]
}

/** Group catalog entries by resource_type, sorted alphabetically. */
const groups = computed<Group[]>(() => {
  const byResource = new Map<string, PermissionEntry[]>()
  for (const entry of props.catalog) {
    const arr = byResource.get(entry.resource_type) ?? []
    arr.push(entry)
    byResource.set(entry.resource_type, arr)
  }
  return Array.from(byResource.entries())
    .map(([resource, entries]) => ({
      resource,
      entries: entries.slice().sort((a, b) => a.action.localeCompare(b.action)),
    }))
    .sort((a, b) => a.resource.localeCompare(b.resource))
})

function formatResource(resource: string): string {
  return resource.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function countSelected(group: Group): number {
  return group.entries.reduce((n, e) => (selected.value.has(e.code) ? n + 1 : n), 0)
}

/**
 * Capability ceiling: an admin can only grant permissions they themselves
 * hold. Superuser bypasses. Already-selected codes stay enabled even if the
 * actor lost the right meanwhile — otherwise the matrix would lock the user
 * out of clearing the box, leaving a stranded grant.
 */
function entryDisabled(entry: PermissionEntry): boolean {
  if (isSuperuser.value) return false
  if (selected.value.has(entry.code)) return false
  return !can(entry.code)
}

function entryTooltip(entry: PermissionEntry): string {
  const parts: string[] = [entry.code]
  if (entry.description) parts.push(entry.description)
  if (entryDisabled(entry)) {
    parts.push("Your role doesn't include this permission.")
  }
  return parts.join(' — ')
}

function toggle(code: string) {
  if (props.readonly) return
  const next = new Set(selected.value)
  if (next.has(code)) {
    next.delete(code)
  } else {
    next.add(code)
  }
  emit('update:modelValue', Array.from(next).sort())
}
</script>

<style scoped>
.opacity-60 {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
