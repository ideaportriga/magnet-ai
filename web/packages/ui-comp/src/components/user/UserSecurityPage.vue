<template lang="pug">
.q-pa-lg(style='max-width: 600px; margin: 0 auto')
  .text-h5.q-mb-lg {{ t.security }}

  //- 2FA section
  q-card.q-mb-md
    q-card-section
      .text-subtitle1.q-mb-md {{ t.twoFactorAuth }}
      .row.items-center.q-mb-sm
        .text-body2 {{ t.status }}
        q-chip.q-ml-sm(
          :color='userInfo?.is_two_factor_enabled ? "positive" : "grey-4"',
          :text-color='userInfo?.is_two_factor_enabled ? "white" : "dark"',
          size='sm'
        ) {{ userInfo?.is_two_factor_enabled ? t.enabled : t.disabled }}

      q-btn(
        v-if='!userInfo?.is_two_factor_enabled',
        outline,
        color='primary',
        :label='t.enable2fa',
        no-caps,
        @click='$emit("setup-mfa")'
      )
      q-btn(
        v-else,
        outline,
        color='negative',
        :label='t.disable2fa',
        no-caps,
        @click='$emit("disable-mfa")'
      )

  //- Active sessions
  q-card.q-mb-md
    q-card-section
      .row.items-center.justify-between.q-mb-md
        .text-subtitle1 {{ t.activeSessions }}
        q-btn(
          v-if='sessions.length > 1',
          flat,
          color='negative',
          :label='t.revokeAllOthers',
          size='sm',
          no-caps,
          @click='$emit("revoke-all-sessions")'
        )

      q-list(separator, v-if='sessions.length > 0')
        q-item(v-for='session in sessions', :key='session.id')
          q-item-section
            q-item-label {{ session.device_info || t.unknownDevice }}
            q-item-label(caption) Since {{ new Date(session.created_at).toLocaleString() }}
          q-item-section(side)
            q-btn(
              flat,
              color='negative',
              :label='t.revoke',
              size='sm',
              no-caps,
              @click='$emit("revoke-session", session.id)'
            )

      .text-caption.text-grey(v-else) {{ t.noActiveSessions }}
</template>

<script lang="ts">
const DEFAULT_T = {
  security: 'Security',
  twoFactorAuth: 'Two-Factor Authentication',
  status: 'Status:',
  enabled: 'Enabled',
  disabled: 'Disabled',
  enable2fa: 'Enable 2FA',
  disable2fa: 'Disable 2FA',
  activeSessions: 'Active Sessions',
  revokeAllOthers: 'Revoke all others',
  unknownDevice: 'Unknown device',
  revoke: 'Revoke',
  noActiveSessions: 'No active sessions',
}
export default {}
</script>

<script setup lang="ts">
import { computed } from 'vue'
import type { SessionInfo, UserInfo } from '@shared/auth'

const props = withDefaults(defineProps<{
  userInfo: UserInfo | null
  sessions: SessionInfo[]
  /** i18n labels — pass translated strings to override English defaults */
  t?: Record<string, string>
}>(), {
  t: () => ({ ...DEFAULT_T }),
})

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

defineEmits<{
  'setup-mfa': []
  'disable-mfa': []
  'revoke-session': [id: string]
  'revoke-all-sessions': []
}>()
</script>
