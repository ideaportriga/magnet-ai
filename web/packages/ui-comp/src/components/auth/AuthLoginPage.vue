<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container(style='width: 360px')
    .row.items-center.q-mb-lg
      km-icon(name='magnet', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm Magnet AI

    //- Local auth form
    .full-width.q-mb-md(v-if='!mfaRequired')
      q-form.q-gutter-sm(@submit.prevent='handleLogin')
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
          :rules='[val => !!val || "Password is required"]',
          autocomplete='current-password'
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
          label='Log in',
          :loading='loginInProgress',
          no-caps
        )

      .row.justify-between.q-mt-sm
        a.text-caption.cursor-pointer.text-primary(tabindex='0', role='button', @click='$emit("navigate", "forgot-password")', @keydown.enter='$emit("navigate", "forgot-password")') Forgot password?
        a.text-caption.cursor-pointer.text-primary(v-if='signupEnabled', tabindex='0', role='button', @click='$emit("navigate", "signup")', @keydown.enter='$emit("navigate", "signup")') Sign up

    //- MFA challenge
    .full-width.q-mb-md(v-else)
      .text-subtitle2.q-mb-sm Enter the 6-digit code from your authenticator app
      q-form(@submit.prevent='handleMfa')
        q-input(
          v-model='mfaCode',
          label='Authentication code',
          outlined,
          dense,
          maxlength='8',
          autocomplete='one-time-code'
        )
        .text-negative.text-caption.q-mt-xs(v-if='errorMessage') {{ errorMessage }}
        q-btn.full-width.q-mt-sm(
          type='submit',
          color='primary',
          label='Verify',
          :loading='loginInProgress',
          no-caps
        )
      a.text-caption.cursor-pointer.text-primary.q-mt-sm(tabindex='0', role='button', @click='mfaRequired = false; errorMessage = ""', @keydown.enter='mfaRequired = false; errorMessage = ""') Back to login

    //- OAuth/OIDC providers divider
    template(v-if='providers.length > 0 && !mfaRequired')
      .row.items-center.full-width.q-my-md
        q-separator.col
        .text-caption.q-mx-sm.text-grey or continue with
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

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import type { AuthClient } from '@shared/auth'

const props = defineProps<{
  authClient: AuthClient
  providers?: string[]
  signupEnabled?: boolean
  /** Base URL for OIDC popup flow (e.g. "http://localhost:8000"). Used for Microsoft/Oracle. */
  oidcBaseUrl?: string
  /** Popup dimensions for OIDC providers */
  popupWidth?: string
  popupHeight?: string
}>()

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
  if (oauthInProgress.value === provider) return `Logging in with ${label}...`
  return `Log in with ${label}`
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

  try {
    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
    const ok = await props.authClient.completeOidc(data)
    if (ok) {
      emit('success')
    } else {
      errorMessage.value = 'Authentication failed'
    }
  } catch {
    errorMessage.value = 'Authentication failed'
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

// --- OAuth redirect flow (Google/GitHub — new backend /api/auth/oauth) ---

async function handleOAuthRedirect(provider: string) {
  oauthInProgress.value = provider
  errorMessage.value = ''
  try {
    const { authorization_url } = await props.authClient.getOAuthUrl(provider)
    window.location.href = authorization_url
  } catch (e: any) {
    errorMessage.value = e.message || 'OAuth failed'
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
    errorMessage.value = e.message || 'Login failed'
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
    errorMessage.value = e.message || 'Invalid code'
  } finally {
    loginInProgress.value = false
  }
}
</script>
