/**
 * System name for a model: `<PROVIDER>_<MODEL>` upper-cased.
 *
 * Provider model ids routinely carry characters `validSystemName` rejects —
 * dots (`gpt-4.1`), slashes (`openai/gpt-4o`), colons (`…-v1:0`). The generic
 * `toUpperCaseWithUnderscores` only replaces whitespace, so a dotted id used to
 * produce a name the New Model dialog then refused, and Import saved it as is.
 * Everything outside `[A-Z0-9_-]` becomes `_`.
 */
export function toModelSystemName(providerSystemName: string | null | undefined, modelName: string): string {
  const joined = [providerSystemName, modelName]
    .map((part) => (part ?? '').trim())
    .filter(Boolean)
    .join('_')
  const name = joined
    .toUpperCase()
    .replace(/[^A-Z0-9_-]+/g, '_')
    .replace(/_{2,}/g, '_')
    .replace(/_+$/, '')
  // `validSystemName` wants a letter or underscore first.
  return /^[0-9-]/.test(name) ? `_${name}` : name
}
