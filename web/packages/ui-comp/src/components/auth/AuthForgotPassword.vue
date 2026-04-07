<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm {{ t.resetPassword }}

    .text-caption.q-mb-md.text-grey {{ t.resetDescription }}

    q-form.full-width.q-gutter-sm(@submit.prevent='handleSubmit')
      q-input(
        v-model='email',
        :label='t.email',
        type='email',
        outlined,
        dense,
        :rules='[val => !!val || t.emailRequired]',
        autocomplete='email'
      )

      .text-positive.text-caption.q-mt-xs(v-if='sent') {{ t.resetLinkSent }}

      q-btn.full-width.q-mt-sm(
        type='submit',
        color='primary',
        :label='sent ? t.resend : t.sendResetLink',
        :loading='inProgress',
        no-caps
      )

    .q-mt-sm
      a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "login")', @keydown.enter='$emit("navigate", "login")') {{ t.backToLogin }}
</template>

<script lang="ts">
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
export default {}
</script>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AuthClient } from '@shared/auth'

const props = withDefaults(defineProps<{
  authClient: AuthClient
  t?: Record<string, string>
}>(), {
  t: () => ({ ...DEFAULT_T }),
})

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const emit = defineEmits<{
  navigate: [page: string]
}>()

const email = ref('')
const inProgress = ref(false)
const sent = ref(false)

async function handleSubmit() {
  // Always show success to prevent email enumeration
  inProgress.value = true
  sent.value = false
  try {
    await props.authClient.forgotPassword(email.value)
  } catch {
    // Swallow errors — never reveal whether the email exists
  } finally {
    sent.value = true
    inProgress.value = false
  }
}
</script>
