<template lang="pug">
.q-pa-lg(style='max-width: 600px; margin: 0 auto')
  .text-h5.q-mb-lg Security

  //- 2FA section
  q-card.q-mb-md
    q-card-section
      .text-subtitle1.q-mb-md Two-Factor Authentication
      .row.items-center.q-mb-sm
        .text-body2 Status:
        q-chip.q-ml-sm(
          :color='userInfo?.is_two_factor_enabled ? "positive" : "grey-4"',
          :text-color='userInfo?.is_two_factor_enabled ? "white" : "dark"',
          size='sm'
        ) {{ userInfo?.is_two_factor_enabled ? 'Enabled' : 'Disabled' }}

      q-btn(
        v-if='!userInfo?.is_two_factor_enabled',
        outline,
        color='primary',
        label='Enable 2FA',
        no-caps,
        @click='$emit("setup-mfa")'
      )
      q-btn(
        v-else,
        outline,
        color='negative',
        label='Disable 2FA',
        no-caps,
        @click='$emit("disable-mfa")'
      )

  //- Active sessions
  q-card.q-mb-md
    q-card-section
      .row.items-center.justify-between.q-mb-md
        .text-subtitle1 Active Sessions
        q-btn(
          v-if='sessions.length > 1',
          flat,
          color='negative',
          label='Revoke all others',
          size='sm',
          no-caps,
          @click='$emit("revoke-all-sessions")'
        )

      q-list(separator, v-if='sessions.length > 0')
        q-item(v-for='session in sessions', :key='session.id')
          q-item-section
            q-item-label {{ session.device_info || 'Unknown device' }}
            q-item-label(caption) Since {{ new Date(session.created_at).toLocaleString() }}
          q-item-section(side)
            q-btn(
              flat,
              color='negative',
              label='Revoke',
              size='sm',
              no-caps,
              @click='$emit("revoke-session", session.id)'
            )

      .text-caption.text-grey(v-else) No active sessions
</template>

<script setup lang="ts">
import type { SessionInfo, UserInfo } from '@shared/auth'

defineProps<{
  userInfo: UserInfo | null
  sessions: SessionInfo[]
}>()

defineEmits<{
  'setup-mfa': []
  'disable-mfa': []
  'revoke-session': [id: string]
  'revoke-all-sessions': []
}>()
</script>
