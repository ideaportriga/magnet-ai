<script setup lang="ts">
/**
 * User menu — clickable avatar that opens a dropdown with profile/security/
 * logout actions. Rewritten on `@ds` (DsDropdownMenu).
 */

import { computed } from 'vue'
import { DsDropdownMenu } from '@ds/primitives'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'

const DEFAULT_T = {
  profile: 'Profile',
  security: 'Security',
  logOut: 'Log out',
}

const props = withDefaults(
  defineProps<{
    userInfo: Record<string, unknown> | null
    /** i18n labels — pass translated strings to override English defaults. */
    t?: Record<string, string>
  }>(),
  { t: () => ({}) },
)

const emit = defineEmits<{
  logout: []
  navigate: [path: string]
}>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const displayEmail = computed(() => {
  if (!props.userInfo) return ''
  return (props.userInfo.email as string) || (props.userInfo.preferred_username as string) || ''
})

const displayName = computed(() => {
  if (!props.userInfo) return ''
  return (props.userInfo.name as string) || displayEmail.value
})

const initials = computed(() => {
  const name = displayName.value
  if (!name) return '?'
  const parts = name.split(/[\s@]/).filter(Boolean)
  if (parts.length >= 2) return (parts[0]![0]! + parts[1]![0]!).toUpperCase()
  return name.substring(0, 2).toUpperCase()
})

const menuItems = computed(() => [
  { label: displayName.value, disabled: true } as const,
  { separator: true } as const,
  { label: t.value.profile, onSelect: () => emit('navigate', '/profile') },
  { label: t.value.security, onSelect: () => emit('navigate', '/profile/security') },
  { separator: true } as const,
  { label: t.value.logOut, tone: 'danger' as const, onSelect: () => emit('logout') },
])
</script>

<template>
  <DsDropdownMenu v-if="userInfo" :items="menuItems" placement="bottom" align="end">
    <template #trigger>
      <button
        type="button"
        class="user-menu__trigger"
        :aria-label="`Account menu for ${displayName}`"
      >
        <span class="user-menu__avatar">{{ initials }}</span>
      </button>
    </template>
  </DsDropdownMenu>
</template>

<style scoped>
.user-menu__trigger {
  display: inline-flex;
  align-items: center;
  background: transparent;
  border: 0;
  padding: 0;
  cursor: pointer;
}
.user-menu__avatar {
  inline-size: 32px;
  block-size: 32px;
  border-radius: 50%;
  background: #5c6bc0;
  color: var(--ds-color-static-white, var(--ds-color-static-white));
  font-size: var(--ds-font-size-label);
  font-weight: var(--ds-font-weight-medium);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
