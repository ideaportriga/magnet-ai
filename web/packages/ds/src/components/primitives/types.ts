export type DsDialogSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'
export type DsTooltipPlacement = 'top' | 'right' | 'bottom' | 'left'

export interface DsDropdownMenuActionItem {
  label?: string
  separator?: boolean
  disabled?: boolean
  tone?: 'neutral' | 'primary' | 'danger'
  icon?: string
  onSelect?: (item: DsDropdownMenuActionItem) => void
}

export interface DsRadioOption {
  value: string
  label: string
  disabled?: boolean
}

export interface DsTabItem {
  value: string
  label: string
  disabled?: boolean
}

export interface DsAccordionItem {
  value: string
  label: string
  disabled?: boolean
}

export interface DsSelectOption {
  value: string
  label: string
  disabled?: boolean
}

export type DsButtonVariant = 'primary' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
export type DsButtonSize = 'md' | 'sm' | 'lg' | 'icon' | 'icon-xs' | 'icon-sm' | 'icon-lg'
export type DsBadgeVariant = 'primary' | 'secondary' | 'destructive' | 'outline'
export type DsAlertVariant = 'default' | 'destructive'
export type DsToggleVariant = 'default' | 'outline'
export type DsToggleSize = 'sm' | 'md' | 'lg'
