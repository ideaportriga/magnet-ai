<script setup lang="ts">
/**
 * Signup page — name + email + password. Rewritten on `@ds`.
 */

import { computed, ref } from 'vue'
import type { AuthClient } from '@shared/auth'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmIcon from '@ds/components/domain/KmIcon.vue'
import KmInput from '@ds/components/domain/KmInput.vue'

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

const props = withDefaults(
  defineProps<{
    authClient: AuthClient
    t?: Record<string, string>
  }>(),
  { t: () => ({}) },
)

const emit = defineEmits<{
  success: []
  navigate: [page: string]
}>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

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
  } catch (e) {
    errorMessage.value = (e as Error).message || t.value.signupFailed
  } finally {
    inProgress.value = false
  }
}
</script>

<template>
  <div class="auth-signup">
    <div class="auth-signup__panel stack" data-gap="lg">
      <header class="cluster gap-sm" data-align="center" data-justify="center">
        <KmIcon name="magnet" width="23" height="25" />
        <span class="auth-signup__brand">{{ t.createAccount }}</span>
      </header>

      <div v-if="registered" class="auth-signup__success stack" data-gap="md">
        <KmGlyph name="check" size="48px" tone="success" />
        <h3 class="auth-signup__success-title">{{ t.accountCreated }}</h3>
        <p class="auth-signup__success-body">{{ t.canLoginNow }}</p>
        <KmBtn :label="t.goToLogin" @click="$emit('navigate', 'login')" />
      </div>

      <form v-else class="stack" data-gap="sm" @submit.prevent="handleSignup">
        <KmInput v-model="name" :label="t.name" autocomplete="name" />
        <KmInput v-model="email" :label="t.email" type="email" autocomplete="email" />
        <KmInput
          v-model="password"
          :label="t.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
        >
          <template #append>
            <button
              type="button"
              class="auth-signup__eye"
              :aria-label="showPassword ? t.hidePassword : t.showPassword"
              @click="showPassword = !showPassword"
            >
              <KmGlyph
                :name="showPassword ? 'eye-off' : 'eye'"
                size="20px"
              />
            </button>
          </template>
        </KmInput>

        <p v-if="errorMessage" class="auth-signup__error">{{ errorMessage }}</p>

        <KmBtn
          type="submit"
          :label="t.signup"
          :loading="inProgress"
          @click="handleSignup"
        />

        <a class="auth-signup__link" tabindex="0" role="button" @click="$emit('navigate', 'login')">
          {{ t.alreadyHaveAccount }}
        </a>
      </form>
    </div>
  </div>
</template>

<style scoped>
.auth-signup { display: flex; align-items: center; justify-content: center; block-size: 100%; }
.auth-signup__panel { inline-size: 360px; padding: var(--ds-space-lg); }
.auth-signup__brand { font-size: var(--ds-font-size-h2); font-weight: var(--ds-font-weight-semibold); }

.auth-signup__success { align-items: center; text-align: center; padding: var(--ds-space-md); }
.auth-signup__success-title { font-size: var(--ds-font-size-h2); font-weight: var(--ds-font-weight-semibold); margin: 0; }
.auth-signup__success-body { font-size: var(--ds-font-size-label); color: var(--ds-color-text-grey); margin: 0; }

.auth-signup__error {
  color: var(--ds-color-error-text);
  font-size: var(--ds-font-size-caption);
  margin: 0;
}
.auth-signup__link {
  font-size: var(--ds-font-size-caption);
  cursor: pointer;
  color: var(--ds-color-primary);
  text-decoration: none;
}
.auth-signup__link:hover { text-decoration: underline; }
.auth-signup__eye {
  display: inline-flex;
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;
}
</style>
