// Keep this empty unless a DS wrapper deliberately needs a temporary legacy
// visual binding while exposing a semantic target API. Any entry is counted by
// `sanctionedTemplateVisualFallbacks` and baseline-guarded against growth.
export const sanctionedTemplateVisualFallbacks = []

const fallbackByPath = new Map(sanctionedTemplateVisualFallbacks.map((entry) => [entry.path, entry]))

export function applyTemplateVisualPropAllowlist(filePath, content) {
  const entry = templateVisualPropAllowlistEntry(filePath)
  if (!entry) return content
  return entry.bindings.reduce((next, binding) => next.replaceAll(binding, ''), content)
}

export function countTemplateVisualPropAllowlist(filePath, content) {
  const entry = templateVisualPropAllowlistEntry(filePath)
  if (!entry) return 0
  return entry.bindings.reduce((total, binding) => total + countOccurrences(content, binding), 0)
}

function templateVisualPropAllowlistEntry(filePath) {
  return fallbackByPath.get(normalizeAllowlistPath(filePath))
}

function normalizeAllowlistPath(filePath) {
  const normalized = filePath.replaceAll('\\', '/')
  if (normalized.startsWith('web/')) return normalized.slice('web/'.length)
  return normalized
}

function countOccurrences(content, needle) {
  let count = 0
  let index = 0
  while (index < content.length) {
    const nextIndex = content.indexOf(needle, index)
    if (nextIndex === -1) break
    count += 1
    index = nextIndex + needle.length
  }
  return count
}
