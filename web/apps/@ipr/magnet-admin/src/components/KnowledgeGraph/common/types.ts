export interface TileOption {
  value: string
  label: string
  icon?: string
  description: string
}

export type DialogSize = 'sm' | 'md' | 'lg' | 'xl'

export type ScheduleInterval = 'none' | 'hourly' | 'daily' | 'weekly'

export interface ScheduleFormState {
  interval: ScheduleInterval
  day: number
  hour: number
  timezone: string
}

export interface ControlOption {
  label: string
  value: string
}
