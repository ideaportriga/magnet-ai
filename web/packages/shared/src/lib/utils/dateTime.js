import { DateTime } from 'luxon'

export const formatDateTime = (val) => {
  if (!val) return '—'
  const dateObject = DateTime.fromISO(val, { zone: 'utc' })
  if (!dateObject.isValid) return '—'
  const localDate = dateObject.setZone(DateTime.local().zoneName)
  const localeDateString = localDate.toLocaleString(DateTime.DATE_SHORT)
  const localeTimeString = localDate.toLocaleString(DateTime.TIME_SIMPLE)
  return `${localeDateString} ${localeTimeString}`
}
