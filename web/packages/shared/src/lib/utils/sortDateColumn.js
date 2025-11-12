export const sortDateColumn = (a, b) => {
  if (!a) return -1
  if (!b) return 1
  return a?.valueOf() - b?.valueOf()
}
