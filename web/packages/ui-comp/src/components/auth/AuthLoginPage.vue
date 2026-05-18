<script setup lang="ts">
/**
 * Login page — local password + SSO providers + MFA challenge. Rewritten on
 * `@ds`. Public surface preserved: `authClient`, `providers`, `signupEnabled`,
 * `t`. Emits `success`, `navigate`.
 */

import { computed, ref } from 'vue'
import KmBtn from '@ds/components/domain/KmBtn.vue'
import KmGlyph from '@ds/components/domain/KmGlyph.vue'
import KmIcon from '@ds/components/domain/KmIcon.vue'
import KmInput from '@ds/components/domain/KmInput.vue'
import KmSeparator from '@ds/components/domain/KmSeparator.vue'

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

interface AuthLoginClient {
  loginLocal(email: string, password: string): Promise<{ mfa_required?: boolean }>
  verifyMfa(code: string): Promise<unknown>
  getSsoUrl(provider: string, returnTo?: string): string
}

interface OAuthProvider { name: string; type?: string; displayName?: string }

const props = withDefaults(
  defineProps<{
    authClient: AuthLoginClient
    providers?: Array<string | OAuthProvider>
    signupEnabled?: boolean
    t?: Record<string, string>
  }>(),
  { providers: () => [], signupEnabled: false, t: () => ({}) },
)

const emit = defineEmits<{
  success: []
  navigate: [page: string]
}>()

const t = computed(() => ({ ...DEFAULT_T, ...props.t }))

const localEnabled = computed(() => props.providers.some((p) => providerName(p) === 'local'))
const ssoProviders = computed(() => props.providers.filter((p) => providerName(p) !== 'local'))

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const mfaCode = ref('')
const mfaRequired = ref(false)
const loginInProgress = ref(false)
const oauthInProgress = ref<string | null>(null)
const errorMessage = ref('')

function providerName(provider: string | OAuthProvider): string {
  return typeof provider === 'string' ? provider : provider.name
}

function providerButtonLabel(provider: string | OAuthProvider): string {
  const name = providerName(provider)
  const display = typeof provider === 'object' ? provider.displayName : null
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

function handleSsoRedirect(provider: string) {
  oauthInProgress.value = provider
  errorMessage.value = ''
  try {
    // Preserve ?return_to=… set by the MCP OAuth bridge (or any backend
    // redirect to /admin/login) so SSO lands back where the flow expects,
    // not on /admin/login. Same-origin / no-// guard mirrors App.vue and
    // the backend SSO start endpoint.
    const params = new URLSearchParams(window.location.search)
    const incomingReturnTo = params.get('return_to')
    const returnTo =
      incomingReturnTo && incomingReturnTo.startsWith('/') && !incomingReturnTo.startsWith('//')
        ? incomingReturnTo
        : window.location.pathname
    window.location.href = props.authClient.getSsoUrl(provider, returnTo)
  } catch (e: any) {
    errorMessage.value = (e as Error).message || t.value.oauthFailed
    oauthInProgress.value = null
  }
}

async function handleLogin() {
  if (loginInProgress.value) return
  loginInProgress.value = true
  errorMessage.value = ''
  try {
    const result = await props.authClient.loginLocal(email.value, password.value)
    if (result.mfa_required) mfaRequired.value = true
    else emit('success')
  } catch (e) {
    errorMessage.value = (e as Error).message || t.value.loginFailed
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
  } catch (e) {
    errorMessage.value = (e as Error).message || t.value.invalidCode
  } finally {
    loginInProgress.value = false
  }
}
</script>

<template>
  <div class="auth-login">
    <div class="auth-login__panel stack" data-gap="lg">
      <header class="cluster gap-sm" data-align="center" data-justify="center">
        <KmIcon name="magnet" width="23" height="25" />
        <span class="auth-login__brand">{{ t.magnetAi }}</span>
      </header>

      <form
        v-if="localEnabled && !mfaRequired"
        class="stack"
        data-gap="sm"
        name="login"
        method="post"
        action="/api/v2/auth/login"
        @submit.prevent="handleLogin"
      >
        <KmInput
          v-model="email"
          :label="t.email"
          type="email"
          name="email"
          autocomplete="username"
          inputmode="email"
        />

        <KmInput
          v-model="password"
          :label="t.password"
          :type="showPassword ? 'text' : 'password'"
          name="password"
          autocomplete="current-password"
        >
          <template #append>
            <button
              type="button"
              class="auth-login__eye"
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

        <p v-if="errorMessage" class="auth-login__error">{{ errorMessage }}</p>

        <KmBtn
          type="submit"
          :label="t.login"
          :loading="loginInProgress"
        />

        <div class="cluster" data-justify="between">
          <a class="auth-login__link" tabindex="0" role="button" @click="$emit('navigate', 'forgot-password')">
            {{ t.forgotPassword }}
          </a>
          <a v-if="signupEnabled" class="auth-login__link" tabindex="0" role="button" @click="$emit('navigate', 'signup')">
            {{ t.signup }}
          </a>
        </div>
      </form>

      <div v-if="mfaRequired" class="stack" data-gap="sm">
        <p class="auth-login__mfa-prompt">{{ t.enterMfaCode }}</p>
        <form class="stack" data-gap="sm" @submit.prevent="handleMfa">
          <KmInput
            v-model="mfaCode"
            :label="t.authenticationCode"
            max-length="8"
            autocomplete="one-time-code"
          />
          <p v-if="errorMessage" class="auth-login__error">{{ errorMessage }}</p>
          <KmBtn type="submit" :label="t.verify" :loading="loginInProgress" @click="handleMfa" />
        </form>
        <a class="auth-login__link" tabindex="0" role="button" @click="(mfaRequired = false), (errorMessage = '')">
          {{ t.backToLogin }}
        </a>
      </div>

      <template v-if="ssoProviders.length && !mfaRequired">
        <div v-if="localEnabled" class="cluster gap-sm" data-align="center">
          <KmSeparator class="auth-login__divider" />
          <span class="auth-login__divider-label">{{ t.orContinueWith }}</span>
          <KmSeparator class="auth-login__divider" />
        </div>

        <div class="stack" data-gap="sm">
          <KmBtn
            v-for="provider in ssoProviders"
            :key="providerName(provider)"
            flat
            input-like
            :loading="oauthInProgress === providerName(provider)"
            :label="providerButtonLabel(provider)"
            @click="handleSsoRedirect(providerName(provider))"
          >
            <span class="cluster gap-sm" data-align="center" data-justify="center">
              <img
                v-if="providerIcon(providerName(provider))"
                :src="providerIcon(providerName(provider))!"
                width="18"
                height="18"
                :alt="providerName(provider)"
              >
              <span>{{ providerButtonLabel(provider) }}</span>
            </span>
          </KmBtn>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.auth-login { display: flex; align-items: center; justify-content: center; block-size: 100%; }
.auth-login__panel { inline-size: 360px; padding: var(--ds-space-lg); }
.auth-login__brand { font-size: var(--ds-font-size-h2); font-weight: var(--ds-font-weight-semibold); }
.auth-login__error {
  color: var(--ds-color-error-text);
  font-size: var(--ds-font-size-caption);
  margin: 0;
}
.auth-login__link {
  font-size: var(--ds-font-size-caption);
  cursor: pointer;
  color: var(--ds-color-primary);
  text-decoration: none;
}
.auth-login__link:hover { text-decoration: underline; }
.auth-login__eye {
  display: inline-flex;
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 0;
}
.auth-login__mfa-prompt { font-size: var(--ds-font-size-label); margin: 0; }
.auth-login__divider { flex: 1; }
.auth-login__divider-label {
  font-size: var(--ds-font-size-caption);
  color: var(--ds-color-text-grey);
  margin-inline: var(--ds-space-sm);
  white-space: nowrap;
}
</style>
