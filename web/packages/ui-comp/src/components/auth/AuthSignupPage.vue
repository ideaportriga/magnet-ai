<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm Create account

    //- Success state
    template(v-if='registered')
      .full-width.text-center.q-pa-md
        q-icon(name='fas fa-check-circle', size='48px', color='positive')
        .text-h6.q-mt-md Account created
        .text-body2.text-grey.q-mt-sm You can now log in with your email and password.
        q-btn.full-width.q-mt-lg(
          color='primary',
          label='Go to login',
          no-caps,
          @click='$emit("navigate", "login")'
        )

    //- Registration form
    template(v-else)
      q-form.full-width.q-gutter-sm(@submit.prevent='handleSignup')
        q-input(
          v-model='name',
          label='Name',
          outlined,
          dense,
          autocomplete='name'
        )
        q-input(
          v-model='email',
          label='Email',
          type='email',
          outlined,
          dense,
          :rules='[val => !!val || "Email is required"]',
          autocomplete='email'
        )
        q-input(
          v-model='password',
          label='Password',
          :type='showPassword ? "text" : "password"',
          outlined,
          dense,
          :rules='[val => val.length >= 8 || "Minimum 8 characters"]',
          autocomplete='new-password'
        )
          template(v-slot:append)
            q-icon(
              :name='showPassword ? "visibility_off" : "visibility"',
              class='cursor-pointer',
              role='button',
              tabindex='0',
              :aria-label='showPassword ? "Hide password" : "Show password"',
              @click='showPassword = !showPassword',
              @keydown.enter='showPassword = !showPassword',
              @keydown.space.prevent='showPassword = !showPassword'
            )

        .text-negative.text-caption.q-mt-xs(v-if='errorMessage') {{ errorMessage }}

        q-btn.full-width.q-mt-sm(
          type='submit',
          color='primary',
          label='Sign up',
          :loading='inProgress',
          no-caps
        )

      .q-mt-sm
        a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "login")', @keydown.enter='$emit("navigate", "login")') Already have an account? Log in
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AuthClient } from '@shared/auth'

const props = defineProps<{
  authClient: AuthClient
}>()

const emit = defineEmits<{
  success: []
  navigate: [page: string]
}>()

const name = ref('')
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const inProgress = ref(false)
const errorMessage = ref('')
const registered = ref(false)

async function handleSignup() {
  if (inProgress.value) return
  inProgress.value = true
  errorMessage.value = ''

  try {
    await props.authClient.signup(email.value, password.value, name.value || undefined)
    registered.value = true
  } catch (e: any) {
    errorMessage.value = e.message || 'Signup failed'
  } finally {
    inProgress.value = false
  }
}
</script>
