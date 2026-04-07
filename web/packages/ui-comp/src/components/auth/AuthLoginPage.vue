<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm {{ t.magnetAi }}

    //- Local auth form
    .full-width.q-mb-md(v-if='!mfaRequired')
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
    template(v-if='providers.length > 0 && !mfaRequired')
      .row.items-center.full-width.q-my-md
        q-separator.col
        .text-caption.q-mx-sm.text-grey {{ t.orContinueWith }}
        q-separator.col

      .column.q-gutter-sm.full-width
        q-btn.full-width(
          v-for='provider in providers',
          :key='provider',
          outline,
          no-caps,
          @click='handleProvider(provider)',
          :loading='oauthInProgress === provider'
        )
          .row.items-center.justify-center.q-gutter-sm
            img(v-if='providerIcon(provider)', :src='providerIcon(provider)', width='18', height='18')
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
import { ref, onUnmounted, computed } from 'vue'
import type { AuthClient } from '@shared/auth'

const props = withDefaults(defineProps<{
  authClient: AuthClient
  providers?: string[]
  signupEnabled?: boolean
  /** Base URL for OIDC popup flow (e.g. "http://localhost:8000"). Used for Microsoft/Oracle. */
  oidcBaseUrl?: string
  /** Popup dimensions for OIDC providers */
  popupWidth?: string
  popupHeight?: string
  /** i18n labels — pass translated strings to override English defaults */
  t?: Record<string, string>
}>(), {
  t: () => ({ ...DEFAULT_T }),
})

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

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

// OIDC popup providers use the existing popup flow (Microsoft, Oracle)
const OIDC_POPUP_PROVIDERS = new Set(['microsoft', 'oracle'])

let popupWindow: Window | null = null
let popupCheckInterval: ReturnType<typeof setInterval> | null = null

onUnmounted(() => {
  window.removeEventListener('message', onPopupMessage)
  if (popupCheckInterval) clearInterval(popupCheckInterval)
})

function providerButtonLabel(provider: string): string {
  const labels: Record<string, string> = {
    microsoft: 'Microsoft',
    oracle: 'Oracle',
    google: 'Google',
    github: 'GitHub',
  }
  const label = labels[provider] || provider
  if (oauthInProgress.value === provider) return t.value.loggingInWith.replace('{provider}', label)
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
  if (OIDC_POPUP_PROVIDERS.has(provider) && props.oidcBaseUrl) {
    handleOidcPopup(provider)
  } else {
    handleOAuthRedirect(provider)
  }
}

// --- OIDC popup flow (Microsoft/Oracle — existing backend /auth/login) ---

function handleOidcPopup(provider: string) {
  if (oauthInProgress.value) return
  oauthInProgress.value = provider
  errorMessage.value = ''

  const width = props.popupWidth || '600'
  const height = props.popupHeight || '400'

  popupWindow = window.open(
    `${props.oidcBaseUrl}/auth/login`,
    'popupLoginWithOAuthProvider',
    `width=${width},height=${height}`,
  )

  window.addEventListener('message', onPopupMessage)

  popupCheckInterval = setInterval(() => {
    if (popupWindow?.closed) {
      cleanup()
    }
  }, 500)
}

async function onPopupMessage(event: MessageEvent) {
  window.removeEventListener('message', onPopupMessage)

  // Validate that the message came from our popup window.
  // We can't strictly check origin because the popup may land on the
  // backend origin (e.g. localhost:8000) after IdP callback, while the
  // opener is on the frontend origin (e.g. localhost:7001).
  // Instead, verify the message source is our popup window.
  if (event.source !== popupWindow) {
    cleanup()
    return
  }

  try {
    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
    const ok = await props.authClient.completeOidc(data)
    if (ok) {
      emit('success')
    } else {
      errorMessage.value = t.value.authFailed
    }
  } catch {
    errorMessage.value = t.value.authFailed
  } finally {
    cleanup()
  }
}

function cleanup() {
  oauthInProgress.value = null
  if (popupCheckInterval) {
    clearInterval(popupCheckInterval)
    popupCheckInterval = null
  }
  window.removeEventListener('message', onPopupMessage)
}

// --- OAuth/SSO redirect flow ---
// For v2: server-side redirect via /api/v2/auth/sso/{provider}
// For v1 compat: API call to get authorization URL then redirect

async function handleOAuthRedirect(provider: string) {
  oauthInProgress.value = provider
  errorMessage.value = ''
  try {
    // Check if authClient has getSsoUrl (v2 client) — use direct redirect
    const client = props.authClient as any
    if (typeof client.getSsoUrl === 'function') {
      window.location.href = client.getSsoUrl(provider)
    } else {
      const { authorization_url } = await props.authClient.getOAuthUrl(provider)
      window.location.href = authorization_url
    }
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
