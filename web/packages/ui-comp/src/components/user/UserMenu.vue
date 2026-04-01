<template lang="pug">
.row.items-center.cursor-pointer(v-if='userInfo')
  //- Avatar circle with initials
  .flex.items-center.justify-center.text-white.text-weight-medium(
    :style='avatarStyle'
  ) {{ initials }}

  q-menu(anchor='bottom right', self='top right')
    q-list(style='min-width: 200px')
      q-item-label.q-pa-md(header)
        .text-subtitle2.text-weight-medium {{ displayName }}
        .text-caption.text-grey {{ displayEmail }}

      q-separator

      q-item(clickable, v-close-popup, @click='$emit("navigate", "/profile")')
        q-item-section(side)
          q-icon(name='person', size='20px')
        q-item-section Profile

      q-item(clickable, v-close-popup, @click='$emit("navigate", "/profile/security")')
        q-item-section(side)
          q-icon(name='security', size='20px')
        q-item-section Security

      q-separator

      q-item(clickable, v-close-popup, @click='$emit("logout")')
        q-item-section(side)
          q-icon(name='logout', size='20px', color='negative')
        q-item-section.text-negative Log out
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  userInfo: Record<string, any> | null
}>()

defineEmits<{
  logout: []
  navigate: [path: string]
}>()

const displayEmail = computed(() => {
  if (!props.userInfo) return ''
  return props.userInfo.email || props.userInfo.preferred_username || ''
})

const displayName = computed(() => {
  if (!props.userInfo) return ''
  return props.userInfo.name || displayEmail.value
})

const initials = computed(() => {
  const name = displayName.value
  if (!name) return '?'
  const parts = name.split(/[\s@]/).filter(Boolean)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
})

const avatarStyle = computed(() => ({
  width: '32px',
  height: '32px',
  borderRadius: '50%',
  backgroundColor: '#5c6bc0',
  fontSize: '13px',
}))
</script>
