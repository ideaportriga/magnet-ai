<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm {{ t.createAccount }}

    //- Success state
    template(v-if='registered')
      .full-width.text-center.q-pa-md
        q-icon(name='fas fa-check-circle', size='48px', color='positive')
        .text-h6.q-mt-md {{ t.accountCreated }}
        .text-body2.text-grey.q-mt-sm {{ t.canLoginNow }}
        q-btn.full-width.q-mt-lg(
          color='primary',
          :label='t.goToLogin',
          no-caps,
          @click='$emit("navigate", "login")'
        )

    //- Registration form
    template(v-else)
      q-form.full-width.q-gutter-sm(@submit.prevent='handleSignup')
        q-input(
          v-model='name',
          :label='t.name',
          outlined,
          dense,
          autocomplete='name'
        )
        q-input(
          v-model='email',
          :label='t.email',
          type='email',
          outlined,
          dense,
          :rules='[val => !!val || t.emailRequired]',
          autocomplete='email'
        )
        q-input(
          v-model='password',
          :label='t.password',
          :type='showPassword ? "text" : "password"',
          outlined,
          dense,
          :rules='[val => val.length >= 8 || t.minPassword]',
          autocomplete='new-password'
        )
          template(v-slot:append)
            q-icon(
              :name='showPassword ? "visibility_off" : "visibility"',
              class='cursor-pointer',
              role='button',
              tabindex='0',
              :aria-label='showPassword ? t.hidePassword : t.showPassword',
              @click='showPassword = !showPassword',
              @keydown.enter='showPassword = !showPassword',
              @keydown.space.prevent='showPassword = !showPassword'
            )

        .text-negative.text-caption.q-mt-xs(v-if='errorMessage') {{ errorMessage }}

        q-btn.full-width.q-mt-sm(
          type='submit',
          color='primary',
          :label='t.signup',
          :loading='inProgress',
          no-caps
        )

      .q-mt-sm
        a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "login")', @keydown.enter='$emit("navigate", "login")') {{ t.alreadyHaveAccount }}
</template>

<script lang="ts">
const DEFAULT_T = {
  createAccount: 'Create account',
  accountCreated: 'Account created',
  canLoginNow: 'You can now log in with your email and password.',
  goToLogin: 'Go to login',
  name: 'Name',
  email: 'Email',
  password: 'Password',
  emailRequired: 'Email is required',
  minPassword: 'Minimum 8 characters',
  hidePassword: 'Hide password',
  showPassword: 'Show password',
  signup: 'Sign up',
  alreadyHaveAccount: 'Already have an account? Log in',
  signupFailed: 'Signup failed',
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
    errorMessage.value = e.message || t.value.signupFailed
  } finally {
    inProgress.value = false
  }
}
</script>
