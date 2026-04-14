<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm {{ t.magnetAi }}

    //- Local auth form
    .full-width.q-mb-md(v-if='!mfaRequired && localEnabled')
      q-form.q-gutter-sm(@submit.prevent='handleLogin')
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
          :rules='[val => !!val || t.passwordRequired]',
          autocomplete='current-password'
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
          :label='t.login',
          :loading='loginInProgress',
          no-caps
        )

      .row.justify-between.q-mt-sm
        a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "forgot-password")', @keydown.enter='$emit("navigate", "forgot-password")') {{ t.forgotPassword }}
        a.text-caption.cursor-pointer.text-primary(v-if='signupEnabled', tabindex='0', role='button', @click='$emit("navigate", "signup")', @keydown.enter='$emit("navigate", "signup")') {{ t.signup }}

    //- MFA challenge
    .full-width.q-mb-md(v-else)
      .text-subtitle2.q-mb-sm {{ t.enterMfaCode }}
      q-form(@submit.prevent='handleMfa')
        q-input(
          v-model='mfaCode',
          :label='t.authenticationCode',
          outlined,
          dense,
          maxlength='8',
          autocomplete='one-time-code'
        )
        .text-negative.text-caption.q-mt-xs(v-if='errorMessage') {{ errorMessage }}
        q-btn.full-width.q-mt-sm(
          type='submit',
          color='primary',
          :label='t.verify',
          :loading='loginInProgress',
          no-caps
        )
      a.text-caption.cursor-pointer.text-primary.q-mt-sm(tabindex='0', role='button', @click='mfaRequired = false; errorMessage = ""', @keydown.enter='mfaRequired = false; errorMessage = ""') {{ t.backToLogin }}

    //- OAuth/OIDC providers divider
    template(v-if='ssoProviders.length > 0 && !mfaRequired')
      .row.items-center.full-width.q-my-md(v-if='localEnabled')
        q-separator.col
        .text-caption.q-mx-sm.text-grey {{ t.orContinueWith }}
        q-separator.col

      .column.q-gutter-sm.full-width
        q-btn.full-width(
          v-for='provider in ssoProviders',
          :key='provider.name || provider',
          outline,
          no-caps,
          @click='handleProvider(provider.name || provider)',
          :loading='oauthInProgress === (provider.name || provider)'
        )
          .row.items-center.justify-center.q-gutter-sm
            img(v-if='providerIcon(provider.name || provider)', :src='providerIcon(provider.name || provider)', width='18', height='18')
            span {{ providerButtonLabel(provider) }}
</template>

<script lang="ts">
const DEFAULT_T = {
  magnetAi: 'Magnet AI',
  email: 'Email',
  password: 'Password',
  emailRequired: 'Email is required',
  passwordRequired: 'Password is required',
  hidePassword: 'Hide password',
  showPassword: 'Show password',
  login: 'Log in',
  forgotPassword: 'Forgot password?',
  signup: 'Sign up',
  enterMfaCode: 'Enter the 6-digit code from your authenticator app',
  authenticationCode: 'Authentication code',
  verify: 'Verify',
  backToLogin: 'Back to login',
  orContinueWith: 'or continue with',
  loginWith: 'Log in with {provider}',
  loggingInWith: 'Logging in with {provider} ...',
  authFailed: 'Authentication failed',
  oauthFailed: 'OAuth failed',
  loginFailed: 'Login failed',
  invalidCode: 'Invalid code',
}
export default {}
</script>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface AuthLoginClient {
  loginLocal(email: string, password: string): Promise<{ mfa_required?: boolean }>
  verifyMfa(code: string): Promise<unknown>
  getSsoUrl(provider: string, returnTo?: string): string
}

const props = withDefaults(defineProps<{
  authClient: AuthLoginClient
  providers?: Array<string | { name: string; type: string; displayName?: string }>
  signupEnabled?: boolean
  /** i18n labels — pass translated strings to override English defaults */
  t?: Record<string, string>
}>(), {
  providers: () => [],
  signupEnabled: false,
  t: () => ({ ...DEFAULT_T }),
})

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const localEnabled = computed(() =>
  props.providers.some(p => (typeof p === 'string' ? p : p.name) === 'local')
)
const ssoProviders = computed(() =>
  props.providers.filter(p => (typeof p === 'string' ? p : p.name) !== 'local')
)

const emit = defineEmits<{
  success: []
  navigate: [page: string]
}>()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const mfaCode = ref('')
const mfaRequired = ref(false)
const loginInProgress = ref(false)
const oauthInProgress = ref<string | null>(null)
const errorMessage = ref('')

function providerButtonLabel(provider: string | { name: string; displayName?: string }): string {
  const name = typeof provider === 'string' ? provider : provider.name
  const display = typeof provider === 'object' && provider.displayName
    ? provider.displayName
    : null
  const fallbackLabels: Record<string, string> = {
    microsoft: 'Microsoft',
    oracle: 'Oracle',
    google: 'Google',
    github: 'GitHub',
  }
  const label = display || fallbackLabels[name] || name
  if (oauthInProgress.value === name) return t.value.loggingInWith.replace('{provider}', label)
  return t.value.loginWith.replace('{provider}', label)
}

function providerIcon(provider: string): string | null {
  const icons: Record<string, string> = {
    microsoft: 'https://learn.microsoft.com/en-us/entra/identity-platform/media/howto-add-branding-in-apps/ms-symbollockup_mssymbol_19.svg',
    google: 'https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg',
    github: 'https://github.githubassets.com/favicons/favicon-dark.svg',
  }
  return icons[provider] || null
}

function handleProvider(provider: string) {
  handleSsoRedirect(provider)
}

// --- SSO redirect flow ---

function handleSsoRedirect(provider: string) {
  oauthInProgress.value = provider
  errorMessage.value = ''

  try {
    window.location.href = props.authClient.getSsoUrl(provider, window.location.pathname)
  } catch (e: any) {
    errorMessage.value = e.message || t.value.oauthFailed
    oauthInProgress.value = null
  }
}

// --- Local auth ---

async function handleLogin() {
  if (loginInProgress.value) return
  loginInProgress.value = true
  errorMessage.value = ''

  try {
    const result = await props.authClient.loginLocal(email.value, password.value)
    if (result.mfa_required) {
      mfaRequired.value = true
    } else {
      emit('success')
    }
  } catch (e: any) {
    errorMessage.value = e.message || t.value.loginFailed
  } finally {
    loginInProgress.value = false
  }
}

async function handleMfa() {
  if (loginInProgress.value) return
  loginInProgress.value = true
  errorMessage.value = ''

  try {
    await props.authClient.verifyMfa(mfaCode.value)
    emit('success')
  } catch (e: any) {
    errorMessage.value = e.message || t.value.invalidCode
  } finally {
    loginInProgress.value = false
  }
}
</script>
