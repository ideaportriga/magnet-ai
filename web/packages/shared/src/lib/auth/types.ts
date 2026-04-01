export interface UserInfo {
  id: string
  email: string
  name: string | null
  avatar_url: string | null
  is_verified: boolean
  is_superuser: boolean
  is_two_factor_enabled: boolean
  roles: string[]
  auth_method: string | null
  last_login_at: string | null
  preferred_username: string | null
  oauth_accounts: OAuthAccountInfo[]
}

export interface OAuthAccountInfo {
  provider: string
  email: string | null
}

export interface LoginResult {
  access_token?: string
  token_type?: string
  user_id?: string
  email?: string
  mfa_required?: boolean
  message?: string
}

export interface SignupResult {
  user_id: string
  email: string
  message: string
}

export interface SessionInfo {
  id: string
  device_info: string | null
  created_at: string
  expires_at: string
}

export interface MfaSetupInfo {
  secret: string
  provisioning_uri: string
  qr_code: string
}

export interface AuthorizationUrlInfo {
  authorization_url: string
  state: string
}
