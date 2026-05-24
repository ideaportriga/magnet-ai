export function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function highlightJson(json: string): string {
  if (!json) return ''
  const escaped = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

  return escaped.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?|[\[\]\{\},])/g,
    (match) => {
      let cls = 'number'
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'key'
          const colonIndex = match.lastIndexOf(':')
          const keyPart = match.substring(0, colonIndex)
          const colonPart = match.substring(colonIndex)
          return `<span class="${cls}">${keyPart}</span><span class="punctuation">${colonPart}</span>`
        } else {
          cls = 'string'
        }
      } else if (/true|false/.test(match)) {
        cls = 'boolean'
      } else if (/null/.test(match)) {
        cls = 'null'
      } else if (/[\[\]\{\},]/.test(match)) {
        cls = 'punctuation'
      }
      return `<span class="${cls}">${match}</span>`
    }
  )
}
