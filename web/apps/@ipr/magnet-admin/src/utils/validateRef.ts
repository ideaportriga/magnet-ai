/**
 * Safely call `.validate()` on a template ref. Falls back to `true`
 * when the ref doesn't exist or doesn't expose a `validate` method —
 * e.g. it wraps a `<km-select>`, `<km-toggle>` or a custom widget
 * that handles its own state. Without this guard, post-Quasar
 * components that no longer expose Quasar's `.validate()` triggered
 * runtime errors like "this.$refs[field]?.validate is not a function"
 * during e2e create flows.
 */
export function validateRef(ref: unknown): boolean {
  const fn = (ref as { validate?: unknown } | null | undefined)?.validate
  return typeof fn === 'function' ? Boolean((fn as () => unknown)()) : true
}
