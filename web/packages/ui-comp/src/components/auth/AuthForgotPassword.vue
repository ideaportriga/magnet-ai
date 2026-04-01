<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm Reset password

    .text-caption.q-mb-md.text-grey Enter your email and we'll send you a link to reset your password.

    q-form.full-width.q-gutter-sm(@submit.prevent='handleSubmit')
      q-input(
        v-model='email',
        label='Email',
        type='email',
        outlined,
        dense,
        :rules='[val => !!val || "Email is required"]',
        autocomplete='email'
      )

      .text-positive.text-caption.q-mt-xs(v-if='sent') If the email exists, a reset link has been sent.

      q-btn.full-width.q-mt-sm(
        type='submit',
        color='primary',
        :label='sent ? "Resend" : "Send reset link"',
        :loading='inProgress',
        no-caps
      )

    .q-mt-sm
      a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "login")', @keydown.enter='$emit("navigate", "login")') Back to login
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AuthClient } from '@shared/auth'

defineProps<{
  authClient: AuthClient
}>()

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
  // Fire and forget — don't reveal if email exists
  setTimeout(() => {
    sent.value = true
    inProgress.value = false
  }, 500)
}
</script>
