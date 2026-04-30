const legacyColorMap: Record<string, string> = {
  primary: 'var(--ds-color-primary)',
  secondary: 'var(--ds-color-secondary)',
  accent: 'var(--ds-color-accent)',
  positive: 'var(--ds-color-success)',
  negative: 'var(--ds-color-error)',
  info: 'var(--ds-color-info)',
  warning: 'var(--ds-color-warning)',
  dark: 'var(--ds-color-black)',
  white: 'var(--ds-color-white)',

  grey: '#bdbdbd',
  'grey-1': '#fafafa',
  'grey-2': '#f5f5f5',
  'grey-3': '#eeeeee',
  'grey-4': '#e0e0e0',
  'grey-5': '#bdbdbd',
  'grey-6': '#9e9e9e',
  'grey-7': '#757575',
  'grey-8': '#616161',
  'grey-9': '#424242',
  'grey-10': '#212121',

  'blue-grey-1': '#eceff1',
  'blue-grey-2': '#cfd8dc',
  'blue-grey-3': '#b0bec5',
  'blue-grey-4': '#90a4ae',
  'blue-grey-5': '#78909c',
  'blue-grey-6': '#607d8b',
  'blue-grey-7': '#546e7a',
  'blue-grey-8': '#455a64',
  'blue-grey-9': '#37474f',
  'blue-grey-10': '#263238',

  blue: '#1976d2',
  green: '#21ba45',
  'green-8': '#2e7d32',
  'teal-7': '#00897b',
  'orange-9': '#e65100',
  red: '#db2828',
  'red-1': '#ffebee',
  'red-8': '#c62828',
  'red-9': '#b71c1c',
  'yellow-1': '#fffde7',
  'yellow-10': '#ffb300',
}

const cssColorPattern = /^(#|rgb\(|rgba\(|hsl\(|hsla\(|oklch\(|oklab\(|lab\(|lch\(|color\(|color-mix\(|var\()/i
const cssKeywordPattern = /^(currentColor|transparent|inherit|initial|revert|revert-layer|unset)$/

export function resolveDsColor(value?: string | null): string | undefined {
  const color = value?.trim()
  if (!color) return undefined

  if (cssColorPattern.test(color) || cssKeywordPattern.test(color)) return color
  if (color.startsWith('--')) return `var(${color})`

  const normalized = color.replace(/_/g, '-').toLowerCase()
  const mapped = legacyColorMap[normalized]
  if (mapped) return mapped

  return `var(--ds-color-${normalized}, ${color})`
}