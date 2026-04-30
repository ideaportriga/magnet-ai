<script setup lang="ts">
/**
 * Forgot-password flow — single email field, "If the email exists, a reset
 * link has been sent." messaging. Rewritten on `@ds`.
 */

import { computed, ref } from 'vue'
import type { AuthClient } from '@shared/auth'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmIcon from '@ds/components/domain/KmIcon.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

const DEFAULT_T = {
  resetPassword: 'Reset password',
  resetDescription: "Enter your email and we'll send you a link to reset your password.",
  email: 'Email',
  emailRequired: 'Email is required',
  resetLinkSent: 'If the email exists, a reset link has been sent.',
  resend: 'Resend',
  sendResetLink: 'Send reset link',
  backToLogin: 'Back to login',
}

const props = withDefaults(
  defineProps<{
    authClient: AuthClient
    t?: Record<string, string>
  }>(),
  { t: () => ({}) },
)

const emit = defineEmits<{
  navigate: [page: string]
}>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const email = ref('')
const inProgress = ref(false)
const sent = ref(false)

async function handleSubmit() {
  // Always show success to prevent email enumeration.
  inProgress.value = true
  sent.value = false
  try {
    await props.authClient.forgotPassword(email.value)
  } catch {
    // Swallow errors — never reveal whether the email exists.
  } finally {
    sent.value = true
    inProgress.value = false
  }
}
</script>

<template>
  <div class="auth-forgot">
    <div class="auth-forgot__panel stack" data-gap="lg">
      <header class="cluster gap-sm" data-align="center" data-justify="center">
        <KmIcon name="magnet" width="23" height="25" />
        <span class="auth-forgot__brand">{{ t.resetPassword }}</span>
      </header>

      <p class="auth-forgot__description">{{ t.resetDescription }}</p>

      <form class="stack" data-gap="sm" @submit.prevent="handleSubmit">
        <KmInput v-model="email" :label="t.email" type="email" autocomplete="email" />

        <p v-if="sent" class="auth-forgot__sent">{{ t.resetLinkSent }}</p>

        <KmBtn
          type="submit"
          :label="sent ? t.resend : t.sendResetLink"
          :loading="inProgress"
          @click="handleSubmit"
        />
      </form>

      <a class="auth-forgot__link" tabindex="0" role="button" @click="$emit('navigate', 'login')">
        {{ t.backToLogin }}
      </a>
    </div>
  </div>
</template>

<style scoped>
.auth-forgot { display: flex; align-items: center; justify-content: center; block-size: 100%; }
.auth-forgot__panel { inline-size: 360px; padding: var(--ds-space-lg); }
.auth-forgot__brand { font-size: var(--ds-font-size-h2); font-weight: var(--ds-font-weight-semibold); }
.auth-forgot__description { font-size: var(--ds-font-size-caption); color: var(--ds-color-text-grey); margin: 0; }
.auth-forgot__sent { color: var(--ds-color-success-text); font-size: var(--ds-font-size-caption); margin: 0; }
.auth-forgot__link {
  font-size: var(--ds-font-size-caption);
  cursor: pointer;
  color: var(--ds-color-primary);
  text-decoration: none;
}
.auth-forgot__link:hover { text-decoration: underline; }
</style>
