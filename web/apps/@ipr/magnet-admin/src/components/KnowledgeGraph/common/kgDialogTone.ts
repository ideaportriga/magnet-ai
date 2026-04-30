import { resolveDsColor } from '@ds'

export type KgDialogTone = 'brand' | 'info' | 'accent' | 'assistant' | 'context' | 'success' | 'warning' | 'danger'

const kgDialogToneColorMap: Record<KgDialogTone, string> = {
  brand: 'primary',
  info: 'blue-7',
  accent: 'teal-7',
  assistant: 'deep-purple-6',
  context: 'purple-7',
  success: 'green-7',
  warning: 'deep-orange-7',
  danger: 'red-8',
}

export function resolveKgDialogToneColor(tone: KgDialogTone = 'brand', legacyColor?: string): string {
  const color = legacyColor || kgDialogToneColorMap[tone]
  return resolveDsColor(color) ?? color
}