import { Config } from '@/pinia/modules/main'

const generateConfig = (baseConfig: any): Config => {
  const { auth: authRaw, api: apiRaw } = baseConfig

  const auth = {
    ...(authRaw ?? {}),
    enabled: String(authRaw?.enabled).toLowerCase() == 'true',
  }

  const aiBridgeUrlBase = apiRaw.aiBridge.baseUrl
  const aiBridgeUrlCommon = `${aiBridgeUrlBase}/api`

  const api = {
    apiRaw,
    aiBridge: {
      baseUrl: aiBridgeUrlBase,
      urlCommon: aiBridgeUrlCommon,
      urlAdmin: `${aiBridgeUrlCommon}/admin`,
      urlUser: `${aiBridgeUrlCommon}/user`,
    },
  }

  const environment = baseConfig.environment ?? ''
  const aiBridgeCredentials = (auth?.enabled ?? true) ? 'include' : null

  const config = {
    auth,
    environment,
    api,
    credentials: aiBridgeCredentials,
    panel: {
      baseUrl: baseConfig.panel?.baseUrl ?? '',
    },
    admin: {
      baseUrl: baseConfig.admin?.baseUrl ?? '',
    },
  }

  return config as Config
}

export default generateConfig
