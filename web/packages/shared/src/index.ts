// i18n
export { initLocale, useLocale } from './lib/i18n'

// Auth
export { createAuthClient, createAuthFetch } from './lib/auth'
export type { AuthClient, UserInfo, LoginResult, SignupResult, SessionInfo, MfaSetupInfo } from './lib/auth'

// Composables

export { default as useAuth } from './lib/composables/useAuth'
export { default as useState } from './lib/composables/useState'
export { default as useValidation, validationProps } from './lib/composables/useValidation'

// boot

export { getComponentList } from './lib/boot/componentList'
export { globalProperties } from './lib/boot/globalProperties'
export { default as initDataSource } from './lib/boot/initDataSource'
export { default as quasarConf } from './lib/boot/quasar'

// utils

export {
  pluralize,
  formatNumber,
  formatDate,
  formatOptions,
  getUrlParameter,
  parseDates,
  hasProps,
  readFileBase64,
  sortAlphabetically,
  daysToDate,
  newShade,
  fetchData,
  toKebabCase,
  deepEqual,
  cleanNewObject,
  toUpperCaseWithUnderscores,
} from './lib/utils/base'

export { transformChromaRequest, transformChromaResponse } from './lib/utils/chromaUtils'
export { formatDateTime } from './lib/utils/dateTime'
export { transformFilterToMongoQuery } from './lib/utils/filterTransformation.js'
export { default as getTabComponent } from './lib/utils/getTabComponent.ts'
export { formatDuration, formatTraceType, convertFiltersToFilterObject } from './lib/utils/index.ts'
export { notify } from './lib/utils/notify'
export {
  mountLog,
  setTheme,
  registerComponents,
  registerGlobalProperties,
  errorHandler,
  getAppHoverDirective,
  registerDirectives,
} from './lib/utils/mountUtils.js'
export { fieldmapToVue, fieldmapToVueMock, convertPropSetToJS, convertJSToPropSet, convertTypes } from './lib/utils/nexusUtils.js'
export { getLabel, getSpecificationItems, toSnakeCase } from './lib/utils/openapiUtils.js'
export { default as patchObject } from './lib/utils/patchObject.js'
export { objToSearchExpr, objToJsFilter } from './lib/utils/query.js'
export { sortDateColumn } from './lib/utils/sortDateColumn.js'
export { required, minLength, validJson, notGreaterThan, notLessThan, noInvisibleChars, validSystemName } from './lib/utils/validationRules.js'
