/**
 * Admin-app validation rules with i18n messages injected via Paraglide.
 * Import from here instead of @shared/utils/validationRules.
 */
import {
  required as _required,
  minLength as _minLength,
  validJson as _validJson,
  notGreaterThan as _notGreaterThan,
  notLessThan as _notLessThan,
  noInvisibleChars as _noInvisibleChars,
  validSystemName as _validSystemName,
} from '@shared/utils/validationRules'
import { m } from '@/paraglide/messages'

export const required = () => _required(m.validation_required())

export const minLength = (min: number) => _minLength(min, m.validation_minLength({ min: String(min) }))

export const validJson = () => _validJson(m.validation_invalidJson())

export const notGreaterThan = (max: number) => _notGreaterThan(max, m.validation_notGreaterThan({ max: String(max) }))

export const notLessThan = (min: number) => _notLessThan(min, m.validation_notLessThan({ min: String(min) }))

export const noInvisibleChars = () =>
  _noInvisibleChars(m.validation_invisibleChars(), m.validation_noLeadingTrailingSpaces())

export const validSystemName = () =>
  _validSystemName(m.validation_invalidSystemName(), {
    spacesMessage: m.validation_systemNameSpaces(),
    invisibleCharsMessage: m.validation_systemNameInvisibleChars(),
  })
