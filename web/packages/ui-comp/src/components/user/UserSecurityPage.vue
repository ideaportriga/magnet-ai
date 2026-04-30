<script setup lang="ts">
/**
 * Security page — 2FA toggle and active session list. Rewritten on `@ds`.
 */

import { computed } from 'vue'
import type { SessionInfo, UserInfo } from '@shared/auth'
import KmBtn from '@ds/components/domain/KmBtn.vue'

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

const props = withDefaults(
  defineProps<{
    userInfo: UserInfo | null
    sessions: SessionInfo[]
    t?: Record<string, string>
  }>(),
  { t: () => ({}) },
)

defineEmits<{
  'setup-mfa': []
  'disable-mfa': []
  'revoke-session': [id: string]
  'revoke-all-sessions': []
}>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))
</script>

<template>
  <div class="user-security-page">
    <h2 class="user-security-page__title">{{ t.security }}</h2>

    <section class="user-security-page__card stack" data-gap="md">
      <h3 class="user-security-page__section-title">{{ t.twoFactorAuth }}</h3>

      <div class="cluster gap-sm" data-align="center">
        <span class="user-security-page__status-label">{{ t.status }}</span>
        <span
          class="user-security-page__chip"
          :data-tone="userInfo?.is_two_factor_enabled ? 'success' : 'neutral'"
        >
          {{ userInfo?.is_two_factor_enabled ? t.enabled : t.disabled }}
        </span>
      </div>

      <div>
        <KmBtn
          v-if="!userInfo?.is_two_factor_enabled"
          flat
          :label="t.enable2fa"
          tone="brand"
          @click="$emit('setup-mfa')"
        />
        <KmBtn
          v-else
          flat
          :label="t.disable2fa"
          tone="danger"
          @click="$emit('disable-mfa')"
        />
      </div>
    </section>

    <section class="user-security-page__card stack" data-gap="md">
      <header class="cluster gap-sm" data-justify="between" data-align="center">
        <h3 class="user-security-page__section-title">{{ t.activeSessions }}</h3>
        <KmBtn
          v-if="sessions.length > 1"
          flat
          tone="danger"
          :label="t.revokeAllOthers"
          size="sm"
          @click="$emit('revoke-all-sessions')"
        />
      </header>

      <ul v-if="sessions.length" class="user-security-page__sessions">
        <li
          v-for="session in sessions"
          :key="session.id"
          class="user-security-page__session cluster gap-md"
          data-justify="between"
          data-align="center"
        >
          <span class="user-security-page__session-meta">
            <span>{{ session.device_info || t.unknownDevice }}</span>
            <span class="user-security-page__session-since">
              Since {{ new Date(session.created_at).toLocaleString() }}
            </span>
          </span>
          <KmBtn
            flat
            tone="danger"
            :label="t.revoke"
            size="sm"
            @click="$emit('revoke-session', session.id)"
          />
        </li>
      </ul>

      <p v-else class="user-security-page__empty">{{ t.noActiveSessions }}</p>
    </section>
  </div>
</template>

<style scoped>
.user-security-page {
  max-inline-size: 600px;
  margin: 0 auto;
  padding: var(--ds-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-md);
}
.user-security-page__title {
  font-size: 22px;
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.user-security-page__card {
  padding: var(--ds-space-lg);
  border: 1px solid var(--ds-color-border);
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-white);
}
.user-security-page__section-title {
  font-size: var(--ds-font-size-body-lg);
  font-weight: var(--ds-font-weight-semibold);
  margin: 0;
}
.user-security-page__status-label { font-size: var(--ds-font-size-body); }
.user-security-page__chip {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--ds-space-sm);
  border-radius: var(--ds-radius-full);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-medium);
}
.user-security-page__chip[data-tone='success'] {
  background: var(--ds-color-success-text);
  color: var(--ds-color-static-white, var(--ds-color-static-white));
}
.user-security-page__chip[data-tone='neutral'] {
  background: var(--ds-color-light);
  color: var(--ds-color-black);
}
.user-security-page__sessions {
  list-style: "";
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  border-block-start: 1px solid var(--ds-color-border);
}
.user-security-page__session {
  border-block-end: 1px solid var(--ds-color-border);
  padding-block: var(--ds-space-sm);
}
.user-security-page__session-meta { display: inline-flex; flex-direction: column; }
.user-security-page__session-since { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); }
.user-security-page__empty { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); margin: 0; }
</style>
